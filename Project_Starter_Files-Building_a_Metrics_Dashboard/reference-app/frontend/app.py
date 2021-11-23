from flask import Flask, json, render_template, request
from jaeger_client import Config
from flask_opentracing import FlaskTracing
# from prometheus_flask_exporter import PrometheusMetrics
from prometheus_flask_exporter.multiprocess import GunicornInternalPrometheusMetrics
import os


app = Flask(__name__)

# uncomment below line for local testing, other wise an error will be thrown 

# os.environ["PROMETHEUS_MULTIPROC_DIR"] = "./"

metrics =  GunicornInternalPrometheusMetrics(app, group_by='endpoint')


metrics.info('app_info', 'Application info', version='1.0.3')

config = Config(
    config={
        'sampler':
        {'type': 'const',
         'param': 1},
                        'logging': True,
                        'reporter_batch_size': 1,}, 
                        service_name="frontend")

jaeger_tracer = config.initialize_tracer()
tracing = FlaskTracing(jaeger_tracer, True, app)

@app.route('/')
@metrics.summary('requests_by_status', 'Request latencies by status',
                 labels={'status': lambda r: r.status_code})
@metrics.histogram('requests_by_status_and_path', 'Request latencies by status and path',
                   labels={'status': lambda r: r.status_code, 'path': lambda: request.path})
@metrics.gauge('in_progress', 'Long running requests in progress')
def homepage():
    return render_template("main.html")


@app.route('/servererror')
@metrics.summary('requests_by_status_servererrror', 'Request latencies by status servererrror',
                 labels={'status': lambda r: r.status_code})
@metrics.histogram('requests_by_status_and_path_servererrror', 'Request latencies by status and path servererrror',
                   labels={'status': lambda r: r.status_code, 'path': lambda: request.path})
@metrics.gauge('in_progress_servererrror', 'Long running requests in progress servererrror' )
def servererror():
    response = app.response_class(
            response=json.dumps({"result":"Internal Error"}),
            status=500,
            mimetype='application/json'
    )
    return response

if __name__ == "__main__":
    app.run()