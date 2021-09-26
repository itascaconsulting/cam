// -*- mode: web -*-
var run_data = [],
    done_count = 0,
    error_count = 0,
    pfile_count = 0,
    pending_count = 0,
    approximate_pending_count = 0,
    allKeys = [];

function start() {
  var async_pending = 0,
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
        console.log("finished async load");
        allKeys.map(function (item) {
          var key = item;
          if (key.startsWith("data/done")) {
            done_count++;
          } else if (key.startsWith("data/pending")) {
            // this is a running case read the object and fill in the table.
            s3.getObject({Bucket: bucket_name, Key: key },
                         function(err, data) {
                           if (err) console.log(err, err.stack); // an error occurred
                           else {
                             var run = JSON.parse(data.Body);
                             var moment_date = moment.unix(run.start_time);
                             var date_str = moment_date.format("lll") + " (" +moment_date.fromNow()+")";

                             table.row.add(
                               $("<tr>")
                                 .append($("<td>").text(run.computer),
                                         $("<td>").attr("data-sort", run.start_time)
                                                  .text(date_str),
                                         $("<td>").text(run.base_file),
                                         $("<td>").text(run.parameter_file)))
                                  .node();
                             table.draw(true);

                           }
            });

            pending_count++;
          } else if (key.startsWith("data/error")) {
            s3.getObject({Bucket: bucket_name, Key: key },
                         function(err, data) {
                           if (err) console.log(err, err.stack); // an error occurred
                           else {
                             var run = JSON.parse(data.Body);
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
            })
            error_count++;
          }
        });
        /* $("#finished").append("<H2>").text(done_count + " Jobs Finished"); */
      }
    });
  }
  var table = $("#running_table").DataTable({
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
}
