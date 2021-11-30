 // -*- mode: web -*-
var run_data = [],
    error_count = 0,
    approximate_pending_count = 0,
    allKeys = [],
    summary_data = new Map(),
    running_count = 0,
    waiting_count = 0;



function start() {
  var async_pending = 0,
      async_pending_kl = 0,
      data0 = "{{WebAppAccessKey}}",
      data1 = "{{WebAppSecretKey}}";
  var s3 = new AWS.S3({accessKeyId: data0,
                       secretAccessKey: data1,
                       region: "{{region}}"}),
      sqs = new AWS.SQS({accessKeyId: data0,
                         secretAccessKey: data1,
                         region: "{{region}}"}),
      bucket_name = "{{DataBucketName}}",
      queue_url = "{{QueueURL}}";

  var sqs_params = {
    QueueUrl: queue_url,
    AttributeNames: ["ApproximateNumberOfMessages"]
  };
  sqs.getQueueAttributes(sqs_params, function(err, data) {
    if (err) console.log(err, err.stack);
    else     {
      approximate_pending_count = data.Attributes.ApproximateNumberOfMessages;
      $("#inqueue").append("<H2>").text(approximate_pending_count + " Jobs in Queue");
    }
  });

  function check_summary(computer_data) {
    var computer_name = computer_data.split("_")[0],
        os = computer_data.split("_")[1];
    if (! summary_data.has(computer_name)) {
      return {os: os, error: 0, running:0, waiting:0,
              longest_run: 1e100, longest_wait: 1e100};
    } else {
      return summary_data.get(computer_name);
    }
  }

  function update_summary(computer_data, data) {
    var computer_name = computer_data.split("_")[0];
    summary_data.set(computer_name, data);
  }

  function add_summary() {
    $("#summary").html("");
    $("#summary").append($("<h2>").text(running_count + " running " + waiting_count + " waiting, and " + error_count + " errors"));
    for (const [key, value] of summary_data) {
      var lr_moment_date = moment.unix(value.longest_run),
          lr_str = lr_moment_date.format("lll") + " (" +lr_moment_date.fromNow()+")",
          lw_moment_date = moment.unix(value.longest_wait),
          lw_str = lw_moment_date.format("lll") + " (" +lw_moment_date.fromNow()+")";
      if (value.longest_wait===1e100) {
        lw_str="";
      }
      table_summary.row.add(
        $("<tr>")
          .append($("<td>").text(key),
                  $("<td>").text(value.os),
                  $("<td>").text(value.running),
                  $("<td>").attr("data-sort", value.longest_run)
                           .text(lr_str),
                  $("<td>").text(value.waiting),
                  $("<td>").attr("data-sort", value.longest_wait)
                           .text(lw_str),
                  $("<td>").text(value.error)))
                   .node();
      table_summary.draw(true);
    }

  }

  function listAllKeys() {
    async_pending++;
    s3.listObjectsV2(params, function (err, data) {
      if (err) {
        console.log(err, err.stack); // an error occurred
      } else {
        var contents = data.Contents;
        contents.forEach(function (content) {
          allKeys.push(content.Key);
        });

        if (data.IsTruncated) {
          params.ContinuationToken = data.NextContinuationToken;
          listAllKeys();
        }
      }
      if (--async_pending==0) {
        allKeys.map(function (item) {
          async_pending_kl++;
          var key = item;
          if (key.startsWith("data/pending")) {
            // this is a running case read the object and fill in the table.
            s3.getObject({Bucket: bucket_name, Key: key },
                         function(err, data) {
                           if (err) console.log(err, err.stack); // an error occurred
                           else {
                             var run = JSON.parse(data.Body);
                             var moment_date = moment.unix(run.start_time);
                             var date_str = moment_date.format("lll") + " (" +moment_date.fromNow()+")";
                             var computer_summary = check_summary(run.computer);
                             computer_summary.running += 1;
                             if (run.start_time < computer_summary.longest_run) {
                               computer_summary.longest_run = run.start_time;
                             }
                             update_summary(run.computer, computer_summary);
                             running_count += 1;
                             table_pending.row.add(
                               $("<tr>")
                                 .append($("<td>").text(run.computer),
                                         $("<td>").attr("data-sort", run.start_time)
                                                  .text(date_str),
                                         $("<td>").text(run.base_file),
                                         $("<td>").text(run.parameter_file)))
                                          .node();
                             table_pending.draw(true);
                           }
                           if (--async_pending_kl==0) {
                             add_summary();
                           }
            });
          } else if (key.startsWith("data/error")) {
            s3.getObject({Bucket: bucket_name, Key: key },
                         function(err, data) {
                           if (err) console.log(err, err.stack); // an error occurred
                           else {
                             var run = JSON.parse(data.Body);
                             var computer_summary = check_summary(run.computer);
                             computer_summary.error += 1;
                             update_summary(run.computer, computer_summary);
                             error_count += 1;
                             var moment_start = moment.unix(run.start_time),
                                 moment_end = moment.unix(run.error_time);
                             var $tr = $('<tr>').append(
                               $('<td>').text(run.computer),
                               $('<td>').text(moment_start.format("lll")),
                               $('<td>').text(moment_end.format("lll")),
                               $('<td>').text(run.parameter_file),
                               $('<td>').html("<details><pre>"+run.exception+"</pre></details>"))
                                                .appendTo('#error_table');

                           }
                           if (--async_pending_kl==0) {
                             add_summary();
                           }
            })
          } else if (key.startsWith("data/waiting")) {
            s3.getObject({Bucket: bucket_name, Key: key },
                         function(err, data) {
                           if (err) console.log(err, err.stack); // an error occurred
                           else {
                             var run = JSON.parse(data.Body);
                             run.computer = key.substring(13, key.length-5);
                             var moment_start = moment.unix(run.time),
                                 date_str = moment_start.format("lll") + " (" +moment_start.fromNow()+")";
                             var computer_summary = check_summary(run.computer);
                             computer_summary.waiting += 1;
                             if (run.time < computer_summary.longest_wait) {
                               computer_summary.longest_wait = run.time;
                             }
                             update_summary(run.computer, computer_summary);
                             waiting_count += 1;
                             table_waiting.row.add(
                               $("<tr>")
                                 .append(
                                   $('<td>').text(key),
                                   $('<td>').attr("data-sort", run.time)
                                            .text(date_str),
                                   $('<td>').text(run.time))).node();
                             table_waiting.draw(true);
                           }
                           if (--async_pending_kl==0) {
                             add_summary();
                           }
            })
          }
        });
      }
    });
  }
  var table_summary = $("#summary_table").DataTable({
    "destroy": true,
    columnDefs: [
      {
        targets: 3,
        data: {
          _: '3.display',
          sort: '3.@data-sort',
          type: '3.@data-sort'
        }
      },
      {
        targets: 5,
        data: {
          _: '5.display',
          sort: '5.@data-sort',
          type: '5.@data-sort'
        }
      }
    ],
    "pageLength": 200,
    "language": {
      "emptyTable": " "
  }});



  var table_pending = $("#running_table").DataTable({
    "destroy": true,
    columnDefs: [
      {
        targets: 2,
        data: {
          _: '2.display',
          sort: '2.@data-sort',
          type: '2.@data-sort'
        }
      },
    ],
    "pageLength": 200,
    "language": {
      "emptyTable": " "
  }});

  var table_waiting = $("#waiting_table").DataTable({
    "destroy": true,
    columnDefs: [
      {
        targets: 2,
        data: {
          _: '2.display',
          sort: '2.@data-sort',
          type: '2.@data-sort'
        }
      },
    ],
    "pageLength": 200,
    "language": {
      "emptyTable": " "
  }});

  document.addEventListener('keydown', function(event) {
    if(event.ctrlKey && event.key == 'k') {
      event.preventDefault();
      $('div.dataTables_filter input').focus();
    }
  });
  $('div.dataTables_filter input').attr("placeholder","Ctrl+k").focus();

  var params = {Bucket: bucket_name, Prefix: "data/pending"};
  listAllKeys();
  params = {Bucket: bucket_name, Prefix: "data/error"};
  listAllKeys();
  params = {Bucket: bucket_name, Prefix: "data/waiting"};
  listAllKeys();
}
