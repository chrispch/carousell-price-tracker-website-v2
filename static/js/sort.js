function quickSort(a, sort_type, n) {
  var i, pivot, sorted = false, return_list, lower_list = [], upper_list = [];
  pivot = a[1].getElementsByTagName("TD")[n];  // a[0] is header row
	console.log(pivot);
  if (sort_type == "string") {
    for (i = 2; i < (a.length-1); i++) {
      if (a[i].getElementsByTagName("TD")[n].innerHTML.toLowerCase() < pivot.innerHTML.toLowerCase()) {
        lower_list.push(a[i]);
      } else if (a[i].getElementsByTagName("TD")[n].innerHTML.toLowerCase() > pivot.innerHTML.toLowerCase()) {
        upper_list.push(a[i]);
      } else if (a[i].getElementsByTagName("TD")[n].innerHTML.toLowerCase() == pivot.innerHTML.toLowerCase()) {
        return_list.push(a[i]);
      }
    }
  } else if (sort_type == "number") {
    for (i = 2; i < (a.length-1); i++) {
      if (parseFloat(a[i].innerHTML) < parseFloat(pivot.innerHTML)) {
        lower_list.push(a[i]);
      } else if (parseFloat(a[i].innerHTML) > parseFloat(pivot.innerHTML)) {
        upper_list.push(a[i]);
      } else if (parseFloat(a[i].innerHTML) == parseFloat(pivot.innerHTM)) {
        return_list.push(a[i]);
      }
    }
  }
  // sort sub-arrays by recursion
	console.log(lower_list);
	if (lower_list.length > 0) {
		console.log("next recursion!")
		quickSort(lower_list, sort_type, n);
	}
	if (upper_list.length > 0) {
		console.log("next recursion!")
	  quickSort(upper_list, sort_type. n);
	}
  // combine sub-arrays
  return_list.unshift(lower_list);
  return_list.push(upper_list);
  // check if any switching has been done
  for (var x = 0; x < a.length; x++) {
    if (return_list[x] != a[x]) {
      sorted = true;
      break;
    }
  }
  return [return_list, sorted];
}

function sortTable(n) {
  var table, rows, sorting_done, sorted_rows, sort_type, x;
  table = document.getElementById("returned-data");
  switching = true;
  // Get sort type depending on whether numbers or strings are being compared
  if (n == 0 || n == 2) {
    sort_type = "string"
  } else if (n == 1) {
    sort_type = "number"
  }
  // Set the sorting direction to ascending:
  dir = "asc";
  // Get all rows
	rows = table.getElementsByTagName("TR");
	// for (var i = 0; i < rows.length; i++) {
	// 	x = rows[i].getElementsByTagName("TD")[n];
	// }
  // Quick sort
	console.log(rows);
	qs = quickSort(rows, sort_type, n);
  sorted_rows = qs[0];
	sorting_done = qs[1];
  if (sorting_done) {
    // Remove unsorted rows
    x.forEach(function(e) {
      table.removeChild(e);
    })
    // Add rows in sorted order to table
    if (dir == "asc") {
      for (var x = 0; x < sorted_rows.length; x++) {
        table.appendChild(sorted_rows[x]);
      }
    } else if (dir == "dsc") {
      for (var y = sorted_rows.length; y > 0; y++) {
        table.appendChild(sorted_rows[y]);
      }
    }
  } else {
    // switch directions
    if (dir == "asc") {
      dir = "dsc"
    } else if (dir == "dsc") {
      dir = "asc"
    }
  }
}
