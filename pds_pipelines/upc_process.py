#!/usr/bin/env python
import os
import sys
import datetime
import logging
from ast import literal_eval
import pytz
import argparse
from glob import glob

import pvl
import json
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from pds_pipelines.available_modules import *
from osgeo import ogr

from pysis import isis
from pysis.exceptions import ProcessError

from pds_pipelines.redis_lock import RedisLock
from pds_pipelines.redis_queue import RedisQueue
from pds_pipelines.process import Process
from pds_pipelines.pvl_utils import load_pvl, find_keyword, PVLDecoderNoScientificNotation
from pds_pipelines.db import db_connect
from pds_pipelines.models import session_scope
from pds_pipelines.models.upc_models import SearchTerms, Targets, Instruments, DataFiles, JsonKeywords, BaseMixin
from pds_pipelines.config import pds_log, workarea, upc_db, lock_obj, upc_error_queue, web_base, archive_base, recipe_base
from pds_pipelines.utils import generate_processes, process, add_process_db, get_isis_id


def getPDSid(infile):
    """
    Use ISIS to get the PDS Product ID of a cube.

    Using ISIS `getkey` is preferred over extracting the Product ID
    using the PVL library because of an edge case where PVL will
    erroneously convert Product IDs from string to floating point.

    Parameters
    ----------
    infile : str
             A string file path from which the Product ID will be extracted.


    Returns
    -------
    prod_id : str
        The PDS Product ID.
    """
    for key in ['product_id', 'productid']:
        try:
            prod_id = isis.getkey(from_=infile, keyword=key, recursive="TRUE")
            break
        except ProcessError as e:
            prod_id = None

    if not prod_id:
        return None

    # in later versions of ISIS, key values are returned as bytes
    if isinstance(prod_id, bytes):
        prod_id = prod_id.decode()
    prod_id = prod_id.replace('\n', '')
    return prod_id



def get_target_name(label):
    """
    Try to extract the target_name from a given PDS label.

    Parameters
    ----------
    label : Object
        Any type of pds object that can be indexed

    Returns
    -------
    target_name : str
        The defined target_name from the label. If this is None a target name
        could not be pulled from the label
    """
    try:
        target_name = label['TARGET_NAME']
    except KeyError as e:
        return None

    return target_name

def get_instrument_name(label):
    """
    Try to extract the instrument_name from a given PDS label.

    Parameters
    ----------
    label : Object
        Any type of pds object that can be indexed

    Returns
    -------
    instrument_name : str
        The defined instrument_name from the label. If this is None an instrument name
        could not be pulled from the label
    """
    # Although PDS3 the INSTRUMENT_NAME keyword, it is missing from some older datasets.
    #  PDS3 defines several (often interchangeable) keywords to
    #  hold instrument name, so try each of them in preferred order and grab the first match.
    # If no match is found, leave as None
    for inst in ['INSTRUMENT_NAME', 'INSTRUMENT_ID']:
        try:
            instrument_name = label[inst]
            break
        except KeyError as e:
            instrument_name = None

    return instrument_name

def get_spacecraft_name(label):
    """
    Try to extract the spacecraft_name from a given PDS label.

    Parameters
    ----------
    label : Object
        Any type of pds object that can be indexed

    Returns
    -------
    spacecraft_name : str
        The defined spacecraft_name from the label. If this is None an spacecraft name
        could not be pulled from the label
    """
    # PDS3 does not require a keyword to hold spacecraft name,
    #  and PDS3 defines several (often interchangeable) keywords to
    #  hold spacecraft name, so try each of them in preferred order and grab the first match.
    # If no match is found, leave as None

    for sc in ['SPACECRAFT_NAME','INSTRUMENT_HOST_NAME','MISSION_NAME','SPACECRAFT_ID','INSTRUMENT_HOST_ID']:
        try:
            spacecraft_name = label[sc]
            break
        except KeyError:
            spacecraft_name = None

    return spacecraft_name

def read_json_footprint(footprint_file):
    with open(footprint_file, 'r') as fp:
        geo_json = json.load(fp)
        geo_str = json.dumps(geo_json['features'][0]['geometry'])

    footprint = ogr.CreateGeometryFromJson(geo_str)
    return footprint.ExportToWkt()

def create_datafiles_atts(label, edr_source, input_cube):
    """
    Creates a DataFiles record attribute dictionary through values from a given
    label

    Parameters
    ----------
    label : Object
        Any type of pds object that can be indexed

    edr_source : str
        Path to the original label source

    input_cube : str
        Path to the cube generated from the data source

    Returns
    -------
    datafile_attributes : dict
        A dict of attributes for a Datafiles record (UPC database table record)
    """
    try:
        # If there exists an array of values, then the first value is the
        #  path to the IMG.
        original_image_ext = os.path.splitext(label['^IMAGE'][0])[-1]
        # Sometimes the actual image file has a lowercase extension but the label lists it as uppercase
        # If a file with the uppercase extension does *not* exist, assume image file is lower case
        source_file_no_ext = os.path.splitext(edr_source)[0]
        img_file = source_file_no_ext + original_image_ext

        if not os.path.exists(img_file):
            img_file = source_file_no_ext + original_image_ext.lower()

        d_label = edr_source
    except (TypeError, KeyError):
        img_file = edr_source
        d_label = None

    datafile_attributes = dict.fromkeys(DataFiles.__table__.columns.keys(), None)

    datafile_attributes['source'] = img_file
    datafile_attributes['detached_label'] = d_label

    # Attempt to get the ISIS serial from the cube
    datafile_attributes['isisid'] = get_isis_id(input_cube)

    # Attempt to get the product id from the original label
    product_id = getPDSid(input_cube)

    datafile_attributes['productid'] = product_id

    return datafile_attributes

def create_search_terms_atts(cam_info_pvl, upc_id, input_cube, footprint_file = '', search_term_mapping={}):
    """
    Creates a SearchTerms record attribute dictionary through values from a given
    caminfo file

    Parameters
    ----------
    cam_info_pvl : str
        Path to the caminfo output from the ISIS program caminfo

    upc_id : int
        upc id from the DataFiles record

    input_cube : str
        Path to the cube generated from the data source

    footprint_file : str
        Path to the file containing the image footprint polygon

    search_term_mapping : dict
        Dict of keys mapping search term record attributes to values on the expected label

    Returns
    -------
    search_term_attributes : dict
        A dict of attributes for a SearchTerms record (UPC database table record)
    """
    search_term_attributes = dict.fromkeys(SearchTerms.__table__.columns.keys(), None)
    search_term_attributes['err_flag'] = True

    if not search_term_mapping:
        search_term_mapping = dict(zip(search_term_attributes.keys(), search_term_attributes.keys()))
        search_term_mapping['isisfootprint'] = 'gisfootprint'

    try:
        pvl_label = load_pvl(cam_info_pvl)
    except Exception as e:
        pvl_label = None

    if pvl_label:
        # For each key in the dictionary, get the related keyword from the keywords object
        for key in search_term_attributes.keys():
            try:
                search_term_attributes[key] = find_keyword(pvl_label, search_term_mapping[key])
            except KeyError:
                search_term_attributes[key] = None

        if os.path.exists(footprint_file):
            search_term_attributes['isisfootprint'] = read_json_footprint(footprint_file)

        search_term_attributes['err_flag'] = False

    search_term_attributes['upcid'] = upc_id

    product_id = getPDSid(input_cube)

    search_term_attributes['pdsproductid'] = product_id

    search_term_attributes['processdate'] = datetime.datetime.now(pytz.utc).strftime(
        "%Y-%m-%d %H:%M:%S")

    search_term_attributes = get_keyword_values(search_term_attributes)

    return search_term_attributes

def get_keyword_values(keywords):
    for k,v in keywords.items():
        try:
            keywords[k] = v.value
        except AttributeError:
            # Intentionally left blank.  If v doesn't have a .value, then it
            #  doesn't need to be converted.
            pass
    return keywords

def create_json_keywords_atts(cam_info_pvl, upc_id, input_file, failing_command, logger):
    """
    Creates a new SearchTerms record through values from a given caminfo file
    and adds the new record to the database

    Parameters
    ----------
    cam_info_pvl : str
        Path to the caminfo output from the ISIS program caminfo

    upc_id : int
        upc id from the DataFiles record

    input_file : str
        Path to the original data file being processed

    failing_command : str
        String presentation of the failing processing command

    logger : Object
        Python logger object from the logging library

    Returns
    -------
    json_keywords_attributes : dict
        A dict of attributes for a JsonKeywords record (UPC database table record)
    """
    try:
        pvl_label = load_pvl(cam_info_pvl, decoder=PVLDecoderNoScientificNotation())
    except Exception as e:
        logger.debug(f"Failed to create upc keywords with: {e}")
        pvl_label = None

    json_keywords_attributes = dict.fromkeys(JsonKeywords.__table__.columns.keys(), None)

    json_keywords_attributes['upcid'] = upc_id

    # If the process was unable to finish the pvl label will not be populated
    # but json can read None as "valid" json so just "error out"
    if pvl_label:
        json_keywords = json.dumps(pvl_label, indent=4, sort_keys=True, default=str)
        json_keywords = json.loads(json_keywords)
    else:
        err_dict = {}
        err_dict['processdate'] = datetime.datetime.now(pytz.utc).strftime(
            "%Y-%m-%d %H:%M:%S")
        err_dict['errortype'] = failing_command
        err_dict['file'] = input_file
        err_dict['errormessage'] = f'Error running {failing_command} on file {input_file}'
        err_dict['error'] = True
        json_keywords = err_dict

    json_keywords_attributes['jsonkeywords'] = json_keywords

    return json_keywords_attributes

def parse_args():
    parser = argparse.ArgumentParser(description='UPC Processing')
    parser.add_argument('--persist', '-p', dest="persist",
                        help="Keep intermediate .cub files.", action='store_true')
    parser.add_argument('--log', '-l', dest="log_level",
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the log level.", default='INFO')
    parser.add_argument('--namespace', '-n', dest="namespace",
                        help="The namespace used for this queue.")
    parser.set_defaults(persist=False)
    args = parser.parse_args()
    return args

def main(user_args):
    upc_session_maker, upc_engine = db_connect(upc_db)

    persist = user_args.persist
    log_level = user_args.log_level
    namespace = user_args.namespace

    try:
        slurm_job_id = os.environ['SLURM_ARRAY_JOB_ID']
        slurm_array_id = os.environ['SLURM_ARRAY_TASK_ID']
    except:
        slurm_job_id = ''
        slurm_array_id = ''

    inputfile = ''
    context = {'job_id': slurm_job_id, 'array_id':slurm_array_id, 'inputfile': inputfile}
    logger = logging.getLogger('UPC_Process')
    level = logging.getLevelName(log_level)
    logger.setLevel(level)
    log_file_handle = logging.FileHandler(pds_log + 'Process.log')
    formatter = logging.Formatter(
        '%(asctime)s - %(job_id)s - %(array_id)s - %(inputfile)s - %(name)s - %(levelname)s, %(message)s')
    log_file_handle.setFormatter(formatter)
    logger.addHandler(log_file_handle)
    logger = logging.LoggerAdapter(logger, context)

    # ***************** Set up logging *****************

    # Redis Queue Objects
    RQ_main = RedisQueue('UPC_ReadyQueue', namespace)
    RQ_error = RedisQueue(upc_error_queue, namespace)
    RQ_work = RedisQueue('UPC_WorkQueue', namespace)

    logger.info("UPC Processing Queue: %s", RQ_main.id_name)

    RQ_lock = RedisLock(lock_obj)
    # If the queue isn't registered, add it and set it to "running"
    RQ_lock.add({RQ_main.id_name: '1'})

    try:
        session = upc_session_maker()
        session.close()
    except TypeError as e:
        logger.error("Unable to create a database session/connection to the upc database: %s", e)
        raise e

    # if there are items in the redis queue
    if int(RQ_main.QueueSize()) > 0 and RQ_lock.available(RQ_main.id_name):
        # get a file from the queue
        item = RQ_main.Qfile2Qwork(RQ_main.getQueueName(), RQ_work.getQueueName())
        inputfile = literal_eval(item)[0]
        archive = literal_eval(item)[1]

        if not os.path.isfile(inputfile):
            RQ_error.QueueAdd(f'Unable to locate or access {inputfile} during UPC processing')
            logger.debug("%s is not a file\n", inputfile)
            exit()

        # Build URL for edr_source
        edr_source = inputfile.replace(workarea, web_base)

        # Update the logger context to include inputfile
        context['inputfile'] = inputfile

        recipe_file = recipe_base + "/" + archive + '.json'
        with open(recipe_file) as fp:
            upc_json = json.load(fp)['upc']
            recipe_string = json.dumps(upc_json['recipe'])
            # Attempt to get the optional search_term_mapping for the upc
            # process
            try:
                search_term_mapping = upc_json['search_term_mapping']
            except KeyError:
                search_term_mapping = {}

        no_extension_inputfile = os.path.splitext(inputfile)[0]
        cam_info_file = no_extension_inputfile + '_caminfo.pvl'
        footprint_file = no_extension_inputfile + '_footprint.json'
        catlab_output = no_extension_inputfile + '_catlab.pvl'

        processes = generate_processes(inputfile,
                                       recipe_string, logger,
                                       no_extension_inputfile=no_extension_inputfile,
                                       catlab_output=catlab_output,
                                       cam_info_file=cam_info_file,
                                       footprint_file=footprint_file)
        failing_command, _ = process(processes, workarea, logger)

        # Some datasets with attached PDS labels cause PVL to hang,
        #  so recipe includes call to dump label using `catlab`
        # If present, use the catlab output as pds_label instead of inputfile
        if os.path.exists(catlab_output):
            pds_label = pvl.load(catlab_output)
        else:
            pds_label = pvl.load(inputfile)


        target_name = get_target_name(pds_label)

        try:
            with session_scope(upc_session_maker) as session:
                target_qobj = Targets.create(session, targetname=target_name,
                                                      displayname=target_name.title(),
                                                      system=target_name)
                target_id = target_qobj.targetid

            instrument_name = get_instrument_name(pds_label)
            spacecraft_name = get_spacecraft_name(pds_label)

            with session_scope(upc_session_maker) as session:
                instrument_qobj = Instruments.create(session, instrument=instrument_name,
                                                              spacecraft=spacecraft_name)
                instrument_id = instrument_qobj.instrumentid

            ######## Generate DataFiles Record ########
            datafile_attributes = create_datafiles_atts(pds_label, edr_source, no_extension_inputfile + '.cub')

            datafile_attributes['instrumentid'] = instrument_id
            datafile_attributes['targetid'] = target_id

            with session_scope(upc_session_maker) as session:
                datafile_qobj = DataFiles.create(session, **datafile_attributes)
                upc_id = datafile_qobj.upcid

            ######## Generate SearchTerms Record ########
            search_term_attributes = create_search_terms_atts(cam_info_file, upc_id, no_extension_inputfile + '.cub', footprint_file, search_term_mapping)

            search_term_attributes['targetid'] = target_id
            search_term_attributes['instrumentid'] = instrument_id

            with session_scope(upc_session_maker) as session:
                SearchTerms.create(session, **search_term_attributes)

            ######## Generate JsonKeywords Record ########
            json_keywords_attributes = create_json_keywords_atts(cam_info_file, upc_id, inputfile, failing_command, logger)

            with session_scope(upc_session_maker) as session:
                JsonKeywords.create(session, **json_keywords_attributes)

        # Handle SQL specific database errors
        except SQLAlchemyError as e:
            logger.error("Database operation failed: %s \nRequeueing (%s, %s)", e, inputfile,  archive)
            RQ_main.QueueAdd((inputfile, archive))
            raise e

        # Disconnect from the engines
        upc_engine.dispose()

        if not persist:
            # Remove all files file from the workarea except for the copied
            # source file
            file_prefix = os.path.splitext(inputfile)[0]
            workarea_files = glob(file_prefix + '*')
            # os.remove(os.path.join(workarea, 'print.prt'))
            for file in workarea_files:
                os.remove(file)

        RQ_work.QueueRemove(item)

    logger.info("UPC processing exited")

if __name__ == "__main__":
    sys.exit(main(parse_args()))
