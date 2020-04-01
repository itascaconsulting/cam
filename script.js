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
      data0 = "AKIA353MYQDSUMBWR2N3",
      data1 = "5EyjORUYtpISOE8FnLyw8SGciBzctnSso84JWqWA";
  var s3 = new AWS.S3({accessKeyId: data0,
                       secretAccessKey: data1,
                       region: 'us-east-2'}),
      sqs = new AWS.SQS({accessKeyId: data0,
                         secretAccessKey: data1,
                         region: 'us-east-2'}),
      bucket_name = 'cam-test-databucket-hj1j9bgt336q',
      queue_url = 'https://sqs.us-east-2.amazonaws.com/820029980901/cam-test-JobQueue-ZFSZVXZQ6HES.fifo';

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
          if (key.startsWith("done")) {
            done_count++;
          } else if (key.startsWith("pending")) {
            // this is a running case read the object and fill in the table.
            s3.getObject({Bucket: bucket_name, Key: key },
                         function(err, data) {
                           if (err) console.log(err, err.stack); // an error occurred
                           else {
                             var run = JSON.parse(data.Body);
                             var moment_date = moment.unix(run.start_time);

                             var $tr = $('<tr>').append(
                               $('<td>').text(run.computer),
                               $('<td>').text(moment_date.format("lll") + " (" +moment_date.fromNow()+")"),
                               $('<td>').text(run.base_file),
                               $('<td>').text(run.parameter_file))
                                                .appendTo('#running_table');
                           }
                         });

            pending_count++;
          } else if (key.startsWith("error")) {
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
  var params = {Bucket: bucket_name, Prefix: "pending"};
  listAllKeys();
  params = {Bucket: bucket_name, Prefix: "error"};
  listAllKeys();
}
