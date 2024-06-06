var SlidenPlotApp = (function() {

  var getters_ = {},
      user_callback = undefined,
      // dictionary mapping short_name to function(new_data) that sets new data
      set_inputs = {},
      internal_callback = function() {
        var new_values = get_values();
        user_callback(new_values); };

  var get_values = function() {
    // Returns the parameters of the app as a dictionary accessed by short name
    var ret = {};
    for (var key in getters_) {
      if (!getters_.hasOwnProperty(key)) continue;
      ret[key] = getters_[key].call();
    }
    return ret;
  };

  var set_values = function(new_data, execute_callback) {
    execute_callback = execute_callback === undefined ? true : execute_callback;
    for (let key in new_data) {
      set_inputs[key](new_data[key]);
    }
    if (execute_callback) {
      user_callback(get_values());
    }
  };

  var set_callback = function(callback) {
    user_callback = callback;
    internal_callback();
  };

  var add_float_slider = function(target, short_name, name, start, min_, max_, options) {
    var min = min_,
        max = max_;
    options = options || {};
    let slider_width = options.slider_width || 300,
        input_width = options.input_width || 100,
        fill = options.fill === undefined ? null : options.fill,
        font_size = options.font_size || 12,
        text_format = options.text_format || d3.format(".6e"),
        units = options.units || "",
        margin = options.margin || "5px",
        text_box_input = true,
        last_valid_text_box_input = undefined;

    if (!(start >= min)) throw "Start must be greater than or equal to min.";
    if (!(start <= max)) throw "Start must be less than or equal to max.";
    if (!(min < max)) throw  "min must be less than max.";
    let slider_div = d3.select(target)
      .append("div")
      .attr("class", "slider_div")
      .attr("style", "width: " + (slider_width) + "px; margin: " + margin);
    let slider_div_header = slider_div.append("div");
    slider_div_header.append("div")
      .text(name)
      .attr("style", "float:left; font-size: " + font_size + "px;");

    // Add info text
    if ("info_text" in options) {
      let info_text_size = options.info_text_size || font_size;
      slider_div_header
        .append("div")
        .attr("id", "info_img_" + short_name)
        .text("?")
        .attr("style", "float:left; margin: 0 0 0 10px;font-size: " + (font_size - 1) + "px; position: relative;" +
              "top: -" + (font_size / 36 * 5) + "px" + "; border: 1px solid blue;" +
              "border-radius: " + (font_size + 2) + "px; width: " + (font_size + 2) + "px;" +
              "height: " + (font_size + 2) + "px; text-align: center;" +
              "color: blue; text-decoration: none; cursor: default");
      slider_div_header
        .append("div")
        .attr('class', 'info')
        .text(options.info_text)
        .attr("style", "border: 1px solid black; background: #cbcbcb; position: absolute;" +
                       "width: " + (-6.67 + slider_width) + "px;font-size: " + info_text_size + "px;" +
                       "padding: 2px 2px; white-space: pre-wrap; border-radius: 6px; z-index: 2;" +
              "transform: translateY(" + (font_size + 5) + "px);");
      // Add hovering style for info
      let style;
      style = document.getElementById("sliders_info_style");
      if (!style) {
        style = document.createElement('style', { is : 'text/css' });
        style.id = "sliders_info_style";
        style.innerHTML = '.info { display: none; } ';
        document.getElementsByTagName('head')[0].appendChild(style);
      }
      style.innerHTML = style.innerHTML + '#info_img_' + short_name + ':hover + .info { display: block; }';
    }

    // when a value is set it should go exactly as is in the text box
    // and that should be the true value. A flag for each slider
    // should say where the true value is. When inputs comes from the
    // slider the text box should be updated, when the text box is
    // updated the value should stay as is and the slider should be
    // set to approximatly the correct position and should not update the text box

    //when set_inputs[short_name]() is called flag text_box_input is true



    // Add input box
    let input_div = slider_div
      .append('div')
        .attr("style", "clear:both;width:" + input_width + "px;");
    var input_box = input_div
        .append("input")
        .attr("name", short_name);
    input_box.attr("type", "number")
      .property('value', text_format(start))
      .property("min", min)
      .property("max", max)
      .property("step", (max - min)/100.0)
      .attr("style", "clear:both;position:static;width: " + input_width + "px; font-size: " + font_size + "px");
    slider_div.append("div").text(units);
    last_valid_text_box_input = start;
    var formatter = (max < 1e3) ? d3.format("") : d3.format(".1e");
    var slider = d3
        .sliderHorizontal()
        .min(min)
        .max(max)
        .step((max-min)/200.0)
        .default(start)
        .width(slider_width * 7 / 8)
        .fill(fill)
        .ticks(5).tickFormat(formatter)
        .displayValue(false)
        .on('onchange.a', function (value)
            {
              // console.log("in slider on change");
              // console.log("slider value = " + value);
              // console.log("text_box_input: " + text_box_input);
              if (! text_box_input) {
                input_box.property("value", text_format(value));
                last_valid_text_box_input = value;
                internal_callback();
              }
            })
        .on('drag', function (value)
            {
              // console.log("in drag");
              // console.log(value);
              // console.log(text_box_input);
              text_box_input = false;
              input_box.property("value", text_format(value));
            })
        .on('end', function (value)
            {
              // console.log("in end");
              // console.log(value);
              // console.log(text_box_input);
              text_box_input = false;
              input_box.property("value", text_format(value));
              last_valid_text_box_input = value;
            });
    getters_[short_name] = (function () {
      //console.log("in getter");
      //console.log(text_box_input);
      if (text_box_input) {
        return parseFloat(input_box.property('value')); //
      } else {
        return slider.value();
      }
    });

    slider_div
      .append('svg')
      .attr('width', slider_width)
      .attr('height', 60)
      .append('g')
      .attr('transform', 'translate(12,20)')
      .call(slider);

    function handle_input_update(newValue) {
      if (!isNaN(newValue) && (newValue <= max) && (newValue >= min)) {
        text_box_input = true;
        input_box.property('value', text_format(newValue));
        slider.value(newValue);
        internal_callback();
        last_valid_text_box_input = newValue;
      } else {
        input_box.property("value", text_format(last_valid_text_box_input));
        input_box.transition().duration(250).style("background-color", "red") .transition().duration(1000).style("background-color", "#FFF");
      }
    }
    // link input box change to slider
    input_box.on("click", function () {
      var newValue = parseFloat(input_box.property('value'));
      handle_input_update(newValue);
    });

    input_box.on("keyup",function (e, b) {
      let codes = ['Enter'];
      if (codes.includes(d3.event.key)) {
        var newValue = parseFloat(input_box.property('value'));
        handle_input_update(newValue);
      }
    });

    input_box.on("focusout", function(e, b) {
      var newValue = parseFloat(input_box.property('value'));
        handle_input_update(newValue);
    });

    set_inputs[short_name] = function(new_data) {
      console.log("in setter");
      text_box_input = true;
      last_valid_text_box_input = new_data;
      slider.value(new_data);
    };
    return slider;
  };

  var add_radio_buttons = function(target, short_name, name, button_names, checked, options) {
    options = options || {};
    let font_size = options.font_size || 12,
        inline = options.inline || false,
        margin = options.margin || "5px 5px";
    let radio_div = d3.select(target)
      .append('div')
      .attr("class", "radio_div")
      .attr('id', 'radio_div_' + short_name)
      .attr("style", "font-size: " + font_size + "px; clear: both; overflow: hidden; margin: " + margin);
    radio_div.append('p')
      .text(name)
      .attr("style", "margin: 0 0;");

    let selections = {};
    for (let i=0; i<button_names.length; i++) {
      let section = radio_div.append("div");
      if (inline) {
        section.attr("style", "float: left; margin: 5px 5px 0 0; height: " + (font_size + 3) + "px");
      } else {
        section.attr("style", "clear: both; margin: 5px 0 0 0; height: " + (font_size + 3) + "px");
      }
      let selection =  section.append("input")
          .attr("type", "radio")
          .attr("name", short_name)
          .attr("value", button_names[i])
          .attr("style", 'float: left; border: 0px; height: ' + font_size + 'px; ' +
                         'width: ' + font_size + 'px; margin-top: 0')
          .on("change", function () { internal_callback(); });
      selections[button_names[i]] = selection;
      section.append("p")
          .text(button_names[i])
          .attr("style", "font-size: " + (font_size - 2) + "px; float: left; margin: 0 0;");
      if (button_names[i]===checked) { selection.attr("checked",""); }
    }
    getters_[short_name] = function () {
      return document.querySelector('input[name="'+short_name+'"]:checked').value;
    };
    set_inputs[short_name] = function(selected_value) { selections[selected_value].attr("checked",""); };

    return radio_div;
  };

  var add_check_box = function(target, short_name, name, checked) {
    let check_box_div = d3.select(target)
      .append('div')
      .text(name)
      .attr('class', 'check_box_div');

    var input =  check_box_div.append("input");
    input.attr("type", "checkbox")
      .attr("name", short_name)
      .attr("value", short_name)
      .on("change", internal_callback);
    if (checked) { input.attr("checked",""); }
    getters_[short_name] = function () { return !!input.property("checked"); };
  };

  var add_input_box = function(target, short_name, long_name, starting_value, options) {
    options = options || {};
    let input_width = options.input_width || 150,
        font_size = options.font_size || 16,
        text_format = options.text_format || d3.format(".6e"),
        inline = options.inline || false,
        margin = options.margin || "5px 5px",
        max = options.max || Number.MAX_VALUE,
        min = options.min || Number.MIN_VALUE,
        step = options.step || 1;

    let input_div = d3.select(target)
      .append("div")
      .attr("class", "input_div")
      .attr("id", "input_div_"+short_name)
      .attr("style", "clear: both; margin: " + margin +
                     ";font-size: " + font_size + "px;");

    // Header
    let header = input_div.append("div")
      .attr('style', 'height: ' + (font_size*1.5) + 'px;');
    header.append("p")
      .text(long_name)
      .attr('style', "margin-right: 5px; float: left; font-size: " + font_size + 'px;');

    // Input box
    let input_box = input_div
        .append("input")
        .attr("name", short_name)
        .attr("type", "number")
        .attr('step', step)
        .property('value', text_format(starting_value));
    if (inline) {
      input_box.attr("style", "float:left;width: " + input_width + "px; font-size: " + font_size + "px;" +
                     "transform: translateY(-12.5%);");
    } else {
      input_box.attr("style", "clear:both;position:static;width: " + input_width + "px; font-size: " + font_size + "px");
    }

    // minimum & maximum
    if ('min' in options) {
      input_box.attr('min', options.min);
    }
    if ('max' in options) {
      input_box.attr('max', options.max);
    }

    // Add info text
    if ("info_text" in options) {
      let info_text_size = options.info_text_size || font_size,
          info_text_width = options.info_text_width || (input_width + 1);
      let info_target;
      let text_style = "border: 1px solid black; background: #cbcbcb; position: absolute;" +
          "padding: 2px 2px; white-space: pre-wrap; border-radius: 6px; z-index: 2;" +
          "font-size: " + info_text_size + "px;";
      if (inline) {
        info_target = input_div;
        text_style += "width: " + info_text_width + "px;" +
          "transform: translateY(" + (font_size + 5) + "px);";
      } else {
        info_target = header;
        text_style += "width: " + info_text_width + "px; transform: translateY(" + (font_size + 4) + "px);";
      }
      info_target.append("div")
          .attr("id", "info_img_" + short_name)
          .text("?")
        .attr("style", "float:left; margin: 0 0 0 5px;font-size: " + (font_size - 1) + "px; position: relative;" +
              "top: -" + (font_size / 36 * 5) + "px" + "; border: 1px solid blue;" +
              "border-radius: " + (font_size + 2) + "px; width: " + (font_size + 2) + "px;" +
              "height: " + (font_size + 2) + "px; text-align: center;" +
              "color: blue; text-decoration: none; cursor: default");
      info_target.append("div")
        .attr('class', 'info')
        .text(options.info_text)
        .attr("style", text_style);
      // Add hovering style for info
      let style;
      style = document.getElementById("sliders_info_style");
      if (!style) {
        style = document.createElement('style', { is : 'text/css' });
        style.id = "sliders_info_style";
        style.innerHTML = '.info { display: none; } ';
        document.getElementsByTagName('head')[0].appendChild(style);
      }
      style.innerHTML = style.innerHTML + '#info_img_' + short_name + ':hover + .info { display: block; }';
    }

    // Handle options
    if ('max' in options) input_box.property("max", options.max);
    if ('min' in options) input_box.property("min", options.min);

    // Link callback to input change
    input_box.on("click", function () {
      let newValue = parseFloat(input_box.property('value'));
      input_box.property('value', text_format(newValue));
      if (newValue) {
        if (newValue <= max && newValue >= min) {
          internal_callback();
        }
      }
    });

    input_box.on("keyup",function (e, b) {
      let codes = ['Enter'];
      if (codes.includes(d3.event.key)) {
        var newValue = parseFloat(input_box.property('value'));
        input_box.property('value', text_format(newValue));
        if (newValue) {
          if (newValue <= max && newValue >= min) {
            internal_callback();
          }
        }
      }
    });

    input_box.on("focusout", function(e, b) {
      var newValue = parseFloat(input_box.property('value'));
      input_box.property('value', text_format(newValue));
      if (newValue) {
        if (newValue <= max && newValue >= min) {
          internal_callback();
        }
      }
    });

    getters_[short_name] = (function () { return parseFloat(input_box.property('value')); });
    set_inputs[short_name] = function(newValue) { input_box.property('value', text_format(newValue)); };
    return input_div;
  };

  var add_drop_down = function(target, short_name, name, selections, options) {
    options = options || {};
    let margin = options.margin || "5px",
        font_size = options.font_size || 14;

    let selector_div = d3.select(target).append('div')
      .attr('class', 'selector_div')
      .attr('style', 'margin: ' + margin + ';');

    let header = selector_div.append('p')
      .text(name)
      .attr('style', 'font-size: ' + font_size + 'px;');

    let selector = selector_div.append('select')
      .attr('name', name)
      .attr('style', 'font-size: ' + font_size + 'px;')
      .on('change', internal_callback);

    let choices = selector.selectAll('option')
      .data(selections)
      .enter()
      .append('option')
      .text(function (e) { return e; });

    getters_[short_name] = function() { return selector.property('value'); };
    set_inputs[short_name] = function(newValue) { selector.property('value', newValue); };
    return selector_div;

  };

  return {
    add_float_slider: add_float_slider,
    add_radio_buttons: add_radio_buttons,
    add_check_box: add_check_box,
    add_input_box: add_input_box,
    add_drop_down: add_drop_down,
    set_callback: set_callback,
    get_values: get_values,
    set_values: set_values
  };

});
