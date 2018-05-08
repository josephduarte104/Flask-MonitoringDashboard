from flask import render_template

from flask_monitoringdashboard import blueprint
from flask_monitoringdashboard.core.auth import secure
from flask_monitoringdashboard.core.plot import get_layout, get_figure, get_margin, heatmap
from flask_monitoringdashboard.core.plot.util import get_information
from flask_monitoringdashboard.database import FunctionCall, session_scope
from flask_monitoringdashboard.database.count_group import count_requests_group, get_value
from flask_monitoringdashboard.database.function_calls import get_endpoints
from flask_monitoringdashboard.database.versions import get_versions

TITLE = 'Distribution of the load per endpoint per version'

AXES_INFO = '''The X-axis presents the versions that are used. The Y-axis presents the 
endpoints that are found in the Flask application.'''

CONTENT_INFO = '''The color of the cell presents the distribution of the number of requests that the 
application received in a single version for a single endpoint. The darker the cell, the more requests 
a certain endpoint has processed in that version. Since it displays the distribution of the load, each 
column sums up to 100%. This information can be used to validate which endpoints processes the most 
requests.'''


@blueprint.route('/version_usage')
@secure
def version_usage():
    return render_template('fmd_dashboard/graph.html', graph=version_usage_graph(), title=TITLE,
                           information=get_information(AXES_INFO, CONTENT_INFO))


def version_usage_graph():
    """
    Used for getting a Heatmap with an overview of which endpoints are used in which versions
    :return:
    """
    with session_scope() as db_session:
        endpoints = get_endpoints(db_session)
        versions = get_versions(db_session)

        requests = [count_requests_group(db_session, FunctionCall.version == v) for v in versions]
        total_hits = []
        hits = [[] for _ in endpoints]
        for hits_version in requests:
            total_hits.append(max(1, sum([value for key, value in hits_version])))

        for j in range(len(endpoints)):
            hits[j] = [0 for _ in versions]
            for i in range(len(versions)):
                hits[j][i] = get_value(requests[i], endpoints[j]) * 100 / total_hits[i]

    layout = get_layout(
        xaxis={'title': 'Versions', 'type': 'category'},
        yaxis={'type': 'category', 'autorange': 'reversed'},
        margin=get_margin()
    )

    trace = heatmap(
        z=hits,
        x=versions,
        y=['{} '.format(e) for e in endpoints],
        colorbar={
            'titleside': 'top',
            'tickmode': 'array',
        }
    )
    return get_figure(layout=layout, data=[trace])
