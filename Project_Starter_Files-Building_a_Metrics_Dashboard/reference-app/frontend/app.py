from flask import Flask, render_template, request
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
common_counter = metrics.counter(
    'by_endpoint_counter', 'Request count by endpoints',
    labels={'endpoint': lambda: request.endpoint})

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
@common_counter
def homepage():
    return render_template("main.html")

metrics.register_default(
    metrics.counter(
        'by_path_counter', 'Request count by request paths',
        labels={'path': lambda: request.path}
    )
)

if __name__ == "__main__":
    app.run()