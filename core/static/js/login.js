function run() {
  var d = new Date();
  var n = d.getDay();
    switch(n) {
        case 1:
            document.getElementById("shift").value = document.getElementById("day1").value;
          break;
        case 2:
            document.getElementById("shift").value = document.getElementById("day2").value;
          break;
        case 3:
            document.getElementById("shift").value = document.getElementById("day3").value;
          break;
        case 4:
            document.getElementById("shift").value = document.getElementById("day4").value;
          break;
        case 5:
            document.getElementById("shift").value = document.getElementById("day5").value;
          break;
        case 6:
            document.getElementById("shift").value = document.getElementById("day6").value;
          break;
        case 0:
            document.getElementById("shift").value = document.getElementById("day7").value;
          break;
      
    }
}


var d = new Date();
var h = d.getHours();
var m = d.getMinutes();
var s = d.getSeconds();
console.log(d);
if (h==13 && m==55 && s==00){
  console.log('Todays shift changed correctly');
  run();
}



