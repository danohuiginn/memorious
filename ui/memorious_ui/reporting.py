import math

from sqlalchemy import func
from sqlalchemy.orm import aliased

from memorious import settings
from memorious.core import session, manager
from memorious.reporting import get_crawler_op_count, get_stage_op_count
from memorious.reporting import get_last_run, is_running, get_crawler_runs
from memorious.model import Event


def global_stats():
    """Stats visible on each page of the UI."""
    stats = {
        'version': settings.VERSION,
        'num_crawlers': len(manager)
    }
    return stats


def crawlers_index():
    """Generate a list of all crawlers, sorted alphabetically, with op
    counts."""
    # query for error and warning events:
    counts = {}
    event = aliased(Event)
    q = session.query(
        event.crawler,
        event.level,
        func.count(event.id),
    )
    q = q.group_by(event.crawler, event.level)
    for (name, level, count) in q:
        if name not in counts:
            counts[name] = {}
        counts[name][level] = count

    # make sure we're including crawlers that have never been run:
    crawlers = []
    for crawler in manager:
        data = counts.get(crawler.name, {})
        data['last_active'] = get_last_run(crawler)
        data['total_ops'] = get_crawler_op_count(crawler)
        data['running'] = is_running(crawler)
        data['crawler'] = crawler
        crawlers.append(data)
    return crawlers


def get_crawler(name):
    return manager.get(name)


def crawler_stages(crawler):
    """See the number of executions of each stage."""
    counts = {}
    # events by level
    evt = aliased(Event)
    q = session.query(
        evt.stage,
        evt.level,
        func.count(evt.id),
    )
    q = q.filter(evt.crawler == crawler.name)
    q = q.group_by(evt.stage, evt.level)
    for (stage_name, level, count) in q:
        if stage_name not in counts:
            counts[stage_name] = {}
        counts[stage_name][level] = count

    stages = []
    for stage in crawler:
        data = counts.get(stage.name, {})
        data['total_ops'] = get_stage_op_count(stage)
        data['stage'] = stage
        stages.append(data)
    return stages


def crawler_events(crawler, run_id=None, level=None, stage=None,
                   page=1, per_page=15):
    evt = aliased(Event)
    q = session.query(evt)
    q = q.filter(evt.crawler == crawler.name)
    if level is not None:
        q = q.filter(evt.level == level)
    if run_id is not None:
        q = q.filter(evt.run_id == run_id)
    if stage is not None:
        q = q.filter(evt.stage == stage)

    total = q.count()
    q = q.order_by(evt.timestamp.desc())
    q = q.limit(per_page)
    q = q.offset((max(1, page) - 1) * per_page)

    return {
        'page': page,
        'per_page': per_page,
        'pages': int(math.ceil((float(total) / per_page))),
        'total': total,
        'results': list(q)
    }


def crawler_runs(crawler):
    runs = get_crawler_runs(crawler)

    # events by level
    evt = aliased(Event)
    q = session.query(
        evt.run_id,
        evt.level,
        func.count(evt.id),
    )
    q = q.filter(evt.crawler == crawler.name)
    q = q.group_by(evt.run_id, evt.level)
    for (run_id, level, count) in q:
        for run in runs:
            if run['run_id'] == run_id:
                run[level] = count
    return runs
