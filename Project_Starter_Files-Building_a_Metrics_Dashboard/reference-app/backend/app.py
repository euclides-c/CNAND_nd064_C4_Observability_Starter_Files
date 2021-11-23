from flask import Flask, render_template, request, jsonify

import pymongo
from flask_pymongo import PyMongo
from jaeger_client import Config
from flask_opentracing import FlaskTracing
import os
# from prometheus_flask_exporter import PrometheusMetrics

from prometheus_flask_exporter.multiprocess import GunicornInternalPrometheusMetrics

app = Flask(__name__)

# uncomment below line for local testing, other wise an error will be thrown 

# os.environ["PROMETHEUS_MULTIPROC_DIR"] = "./"

metrics =  GunicornInternalPrometheusMetrics(app, group_by='endpoint')
metrics.info('app_info', 'Application info', version='1.0.3')
common_counter = metrics.counter(
    'by_endpoint_counter', 'Request count by endpoints',
    labels={'endpoint': lambda: request.endpoint}
)

config = Config(
    config={
        'sampler':
        {'type': 'const',
         'param': 1},
                        'logging': True,
                        'reporter_batch_size': 1,}, 
                        service_name="backend")

jaeger_tracer = config.initialize_tracer()
tracing = FlaskTracing(jaeger_tracer, True, app)

app.config['MONGO_DBNAME'] = 'example-mongodb'
app.config['MONGO_URI'] = 'mongodb://example-mongodb-svc.default.svc.cluster.local:27017/example-mongodb'

mongo = PyMongo(app)

@app.route('/')
@common_counter
def homepage():
    with jaeger_tracer.start_span('hello world') as span:
        hw = "Hello World"
        span.set_tag('message', "Hello World")
    return "Hello World"


@app.route('/api')
@common_counter
def my_api():
    with jaeger_tracer.start_span('api') as span:
        answer = "something"
        span.set_tag('message', answer)
        return jsonify(repsonse=answer)

@app.route('/star', methods=['POST'])
@common_counter
def add_star():
    with jaeger_tracer.start_span('star') as span:
        star = mongo.db.stars
        name = request.json['name']
        distance = request.json['distance']
        star_id = star.insert({'name': name, 'distance': distance})
        new_star = star.find_one({'_id': star_id })
        output = {'name' : new_star['name'], 'distance' : new_star['distance']}
        span.set_tag('status', 'star')
        return jsonify({'result' : output})


# register additional default metrics

metrics.register_default(
    metrics.counter(
        'by_path_counter', 'Request count by request paths',
        labels={'path': lambda: request.path}
    )
)

if __name__ == "__main__":
    
    app.run()
