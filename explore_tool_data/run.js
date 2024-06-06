var my_app = SlidenPlotApp(),
    variables = [["c0", "Layer 0", .5e5, 1e5, 5e5, "Cohesion of layer 0."],
                 ["c1", "Layer 1", .5e5, 1e5, 5e5, "Cohesion of layer 1."],
                 ["c2", "Layer 2", .5e5, 1e5, 5e5, "Cohesion of layer 2."],
                 ["c3", "Layer 3", .5e5, 1e5, 5e5, "Cohesion of layer 3."],
                 ["c4", "Layer 4", .5e5, 1e5, 5e5, "Cohesion of layer 4."],
];



for (var i=0; i<variables.length; i++) {
  // create a div for each input
  var ldiv = $("<div>", {id: 'layer'+i,
                         class:"flex-container"}),
      name = variables[i][0],
      full_name = variables[i][1],
      lower = variables[i][2],
      start = variables[i][3],
      upper = variables[i][4],
      tool_tip = variables[i][5];

  ldiv.append($("<div>", {id: 'ic'+i}));
  ldiv.append($("<div>", {id: 'slider'+i}));
  $("#inputs").append(ldiv);

  my_app.add_float_slider("#ic"+i, "c"+i, full_name, start, lower, upper,
                          options={slider_width: 500,
                                   input_width: 150,
                                   text_format: d3.format("f"),
                                   info_text: tool_tip
                                  });
}

function my_callback(data) {
  var raw_features = [],
      features = [];
  for (var i=0; i<variables.length; i++) {
    var value = data["c"+i];
    raw_features.push(value);
    features.push((value-xscale_mean[i])/xscale_scale[i]);
  }
  var prediction = reg.predict(features),
      ret = prediction;
  console.log(ret);

  $("#result").text("Normalized failure load: "+ret.toFixed(1));

}

my_app.set_callback(my_callback);
