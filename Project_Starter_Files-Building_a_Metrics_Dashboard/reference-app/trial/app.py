from flask import Flask, json, render_template, request, jsonify

from jaeger_client import Config
from jaeger_client.metrics.prometheus import PrometheusMetricsFactory
from opentelemetry import trace
from opentelemetry.exporter import jaeger
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
# from opentelemetry.instrumentation.flask import FlaskInstrumentor
# from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleExportSpanProcessor,
)
import logging
import requests

from prometheus_flask_exporter.multiprocess import GunicornInternalPrometheusMetrics
import os

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    SimpleExportSpanProcessor(ConsoleSpanExporter())
)

app = Flask(__name__)

# uncomment below line for local testing, other wise an error will be thrown 

# os.environ["PROMETHEUS_MULTIPROC_DIR"] = "./"

metrics =  GunicornInternalPrometheusMetrics(app, group_by='endpoint')
metrics.info('app_info', 'Application info', version='1.0.3')
# common_counter = metrics.counter(
#     'by_endpoint_counter', 'Request count by endpoints',
#     labels={'endpoint': lambda: request.endpoint})
# FlaskInstrumentor().instrument_app(app)
# RequestsInstrumentor().instrument()


#config = Config(
#        config={},
#        service_name='your-app-name',
#        validate=True,
#        metrics_factory=PrometheusMetricsFactory(service_name_label='your-app-name')
#)
#tracer = config.initialize_tracer()

def init_tracer(service):
    logging.getLogger('').handlers = []
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)

    config = Config(
        config={
            'sampler': {
                'type': 'const',
                'param': 1,
            },
            'logging': True,
        },
        service_name=service,
    )

    # this call also sets opentracing.tracer
    return config.initialize_tracer()

tracer = init_tracer('trial-service')

@app.route('/')
@metrics.summary('requests_by_status', 'Request latencies by status',
                 labels={'status': lambda r: r.status_code})
@metrics.histogram('requests_by_status_and_path', 'Request latencies by status and path',
                   labels={'status': lambda r: r.status_code, 'path': lambda: request.path})
@metrics.gauge('in_progress', 'Long running requests in progress')
def homepage():
    # return render_template("main.html")
    with tracer.start_span('get-python-jobs') as span:
        homepages = []
        res = requests.get('https://jobs.github.com/positions.json?description=python')
        span.set_tag('first-tag', len(res.json()))
        for result in res.json():
            try:
                homepages.append(requests.get(result['company_url']))
            except:
                return "Unable to get site for %s" % result['company']
    return jsonify(homepages)
            
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
# metrics.register_default(
#     metrics.counter(
#         'by_path_counter', 'Request count by request paths',
#         labels={'path': lambda: request.path}
#     )
# )
if __name__ == "__main__":
    app.run(debug=True,)