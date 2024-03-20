# gtraces-LLM

## Google Traces
This work utilizes Google workload traces to evaluate memory technologies. The traces were collected by DynamoRIO. Mor4e information on the traces can be found [here](https://dynamorio.org/google_workload_traces.html)

### Downloading Google Traces
In order to download the google traces we will be using gsutil. gsutil allows accessing Google Cloud Storage from the command line. A guide to installing gsutils can be found [here](https://cloud.google.com/storage/docs/gsutil_install#linux). Be sure to select the OS you are using to find the correct guide.

Once gsutil is installed we can now use it to download the Google Traces. From a web browser you can find the Cloud Bucket with the traces at [Google workload trace folder](https://console.cloud.google.com/storage/browser/external-traces). The gsutil URL is gs://external-traces. Because we are specifically looking for memory traces the command we will use to copy a given workload is:
```bash 
gsutil ls gs://external-traces/delta/trace-1/ | grep 'mem' | xargs -I '{}' gsutil cp '{}' my_delta 
```

where delta is the workload, trace-1 is the trace we want and my_delta is the path to the directory we want to download to. Congratulations you have successfully downloaded the google traces!

### Running the Google Traces
For this work we will be using the config script drtrace.py. An example with some of the command line arguments you need to use can be found in run_google_traces.sh This script has the abillities to use HBM2, LLM and DDR4. Feel free to add other memory technologies you'd like to test.
