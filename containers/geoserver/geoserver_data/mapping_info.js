// features will contain all objects
// just iterate through it like an array
// make sure to use JSON.parse() to get an object you can select from
// how will it handle the coordinates category?
  // is this something I would need to worry about iterating through or could I just give the file the array?

var json_request = new XMLHttpRequest();

// gets the data from geoserver by sending a request to get the geojson data
var url = "http://localhost:8080/geoserver/PDS/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=PDS%3Aeuropa_view&maxFeatures=50&outputFormat=application%2Fjson";
json_request.open("GET", url, true);
json_request.send();
//console.log("finished");
var data;
json_request.onload = function()
{
  data = json_request.response;
  //console.log(data);
  addToTable();
}


function addToTable()
{
  var table = document.getElementById("planet_table");
  var json_keyword_table = document.getElementById("json_table");
  var geometry_table = document.getElementByID("geometry_table");

	// get the url and load the data into a variable
	// loop through

	// need to add items to elements

  // everything in geojson
  const all_json = JSON.parse(data);
  // just the elements in features
	const elements = all_json.features;
  //console.log(elements);
  //console.log(elements.length);

  //console.log(elements[0].properties.displayname);



  // to remove / character, use replace('/', '')
	let row_index = 1;
  let new_row_index = 0;

	for (i=0; i<elements.length; i++)
	{
    let item = elements[i];
		//let object = JSON.parse(item);

		if (item)
		{
			var new_row = table.insertRow(row_index);
      new_row_index = row_index;
			row_index++;

			// do I need to insert a cell? Can I just change the info?
			//var value_1 = new_row.insertCell(0);

			//var columns = table.rows[new_row_index].cells;
      //console.log(columns.length);

      /*
      var id_column = new_row.insertCell(0);
      var upcid_column = new_row.insertCell(1);
      var isisid_column = new_row.insertCell(2);
      var productid_column = new_row.insertCell(3);
      var source_column = new_row.insertCell(4);
      var detached_label_column = new_row.insertCell(5);
      var instrument_column = new_r
      */

      // adds 11 columns to the new row
      for (column_index = 0; column_index < 12; column_index++)
      {
        new_row.insertCell(column_index);
      }

      // gets the columns for the new row
      var columns = table.rows[new_row_index].cells;

      // adds data to the columns
			columns[0].innerHTML = item.id;
      columns[1].innerHTML = item.properties.upcid;
      columns[2].innerHTML = item.properties.isisid;
      columns[3].innerHTML = item.properties.productid;
      columns[4].innerHTML = item.properties.source;
      columns[5].innerHTML = item.properties.detached_label;
      columns[6].innerHTML = item.properties.instrument;
      columns[7].innerHTML = item.properties.displayname;
      columns[8].innerHTML = item.properties.mission;
      columns[9].innerHTML = item.properties.spacecraft;
      columns[10].innerHTML = item.properties.targetname;

      // parses the jsonkeywords
      //json_key = JSON.parse(item.properties.jsonkeywords);
      //columns[11].innerHTML = JSON.stringify(json_key);

      // parses the jsonkeywords
      json_keys = JSON.parse(item.properties.jsonkeywords);
      //console.log(json_keys);
      //console.log(json_keys.caminfo);
      //console.log(json_keys.caminfo.camstats);
      //console.log(JSON.stringify(json_keys.caminfo));

      var new_json_row = json_keyword_table.insertRow(new_row_index);

      for (json_column_index = 0; json_column_index < 14; json_column_index++)
      {
        new_json_row.insertCell(json_column_index);
      }

      var json_columns = json_keyword_table.rows[new_row_index].cells;

      json_columns[0].innerHTML = JSON.stringify(json_keys.caminfo.camstats.localtimemaximum);
      json_columns[1].innerHTML = JSON.stringify(json_keys.caminfo.camstats.localtimeminimum);
      json_columns[2].innerHTML = JSON.stringify(json_keys.caminfo.camstats.maximumemission);
      json_columns[3].innerHTML = JSON.stringify(json_keys.caminfo.camstats.maximumincidence);
      json_columns[4].innerHTML = JSON.stringify(json_keys.caminfo.camstats.maximumlongitude);
      json_columns[5].innerHTML = JSON.stringify(json_keys.caminfo.camstats.maximumlatitude);
      json_columns[6].innerHTML = JSON.stringify(json_keys.caminfo.camstats.maximumphase);
      json_columns[7].innerHTML = JSON.stringify(json_keys.caminfo.camstats.maximumresolution);
      json_columns[8].innerHTML = JSON.stringify(json_keys.caminfo.camstats.minimumemission);
      json_columns[9].innerHTML = JSON.stringify(json_keys.caminfo.camstats.minimumincidence);
      json_columns[10].innerHTML = JSON.stringify(json_keys.caminfo.camstats.minimumlongitude);
      json_columns[11].innerHTML = JSON.stringify(json_keys.caminfo.camstats.minimumlatitude);
      json_columns[12].innerHTML = JSON.stringify(json_keys.caminfo.camstats.minimumphase);
      json_columns[13].innerHTML = JSON.stringify(json_keys.caminfo.camstats.minimumresolution);



      for (column_index = 0; column_index < 12; column_index++)
      {
        new_row.insertCell(column_index);
      }
      var geomentry_index = geometry_table.rows[new_row_index].cells;

      /*
      json_columns[0].innerHTML = JSON.stringify(json_keys.caminfo.camstats);
      json_columns[1].innerHTML = JSON.stringify(json_keys.caminfo.geometry);
      json_columns[2].innerHTML = json_keys.caminfo.isislabel;
      json_columns[3].innerHTML = json_keys.caminfo.originallabel;
      json_columns[4].innerHTML = json_keys.caminfo.parameters;
      json_columns[5].innerHTML = json_keys.caminfo.polygon;
      json_columns[6].innerHTML = json_keys.caminfo.statistics;
      */
		}
	}

  /*
  for (json_item in json_keys)
  {
    // need to add the json data to another table
    // this should be inside the other loop
  }
  */



	// can I take the amount of columns that already exist in the table and then
	// use that to find the number of rows?
	// since the object info is specific this might not work
	// object.value
}
