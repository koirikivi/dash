#!/usr/bin/env python3
from datetime import datetime
from collections import namedtuple
import pickle
import os
import sys


## Utils

now = datetime.now


def search(set_, **kwargs):
    """Find an item from set based on kwargs"""
    for item in set_:
        if all(getattr(item, attr_name) == expected
               for (attr_name, expected) in kwargs.items()):
            return item
    return None


def replace(set_, item, **kwargs):
    """Replace an item (namedtuple) in a set based on kwargs"""
    new_item = item._replace(**kwargs)
    set_.remove(item)
    set_.add(new_item)


## LIB


Meta = namedtuple("Meta", ["current_project"])


Record = namedtuple("Record", [
    "project",
    "phase",
    "start",
    "end",
])


Project = namedtuple("Project", ["name"])


def ensure_paths():
    data_dir = os.path.join(os.path.expanduser("~"), ".dash")
    meta_file = os.path.join(data_dir, "meta")
    projects_file = os.path.join(data_dir, "projects")
    records_file = os.path.join(data_dir, "records")

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    if not os.path.exists(meta_file):
        meta = Meta(current_project=None)
        with open(meta_file, "wb") as f:
            pickle.dump(meta, f)

    for path in [projects_file, records_file]:
        if not os.path.exists(path):
            with open(path, "wb") as f:
                pickle.dump(set(), f)

    return data_dir, meta_file, projects_file, records_file


def load():
    data_dir, meta_file, projects_file, records_file = ensure_paths()
    with open(meta_file, "rb") as f:
        meta = pickle.load(f)
    with open(projects_file, "rb") as f:
        projects = pickle.load(f)
    with open(records_file, "rb") as f:
        records = pickle.load(f)
    return meta, projects, records


def save(meta=None, projects=None, records=None):
    data_dir, meta_file, projects_file, records_file = ensure_paths()
    for data, path in ((meta, meta_file), (projects, projects_file),
                       (records, records_file)):
        if data is not None:
            with open(path, "wb") as f:
                pickle.dump(data, f)


def get_current_project(meta, projects):
    if meta.current_project is None:
        return None
    return search(projects, name=meta.current_project)


def filter_project_records(project, records):
    return filter(lambda r: r.project == project.name, records)


def get_last_record(project, records):
    records = filter_project_records(project, records)
    try:
        return max(records, key=lambda r: r.start)
    except ValueError:  # empty sequence
        return None


## CLI


def require_current_project(meta, projects):
    project = get_current_project(meta, projects)
    if not project:
        sys.exit("Current project not set")
    return project


def delta_str(delta):
    hours, seconds = divmod(delta.total_seconds(), 3600)
    return "{0:2d}:{1:02d}".format(int(hours), int(seconds / 60 + 0.5))


def project(project_name=None):
    """print, create or switch project"""
    meta, projects, records = load()
    if not project_name:
        print("Current project: {0}".format(meta.current_project))
        return
    project = search(projects, name=project_name)
    if project is not None:
        print("Setting project to {0}".format(project.name))
    else:
        project = Project(name=project_name)
        projects.add(project)
        print("Creating project {0}".format(project.name))
    meta = meta._replace(current_project=project_name)
    save(meta, projects, records)


def start(phase=None):
    """start an activity in a phase or resume previously stopped one"""
    meta, projects, records = load()
    project = require_current_project(meta, projects)

    last_record = get_last_record(project, records)
    if phase is None and last_record is None:
        print("Last record not found - phase required")
        return 1

    time = now()
    if last_record and last_record.end is None:
        # Already working on a task that hasn't ended
        if phase is None or phase == last_record.phase:
            # Need not to do anything
            return 0
        else:
            # Implicitly stop work on previous task
            replace(records, last_record, end=time)
    elif phase is None:
        phase = last_record.phase

    record = Record(start=time, end=None, phase=phase, project=project.name)
    records.add(record)
    save(records=records)


def end():
    """end previous activity"""
    meta, projects, records = load()
    project = require_current_project(meta, projects)
    last_record = get_last_record(project, records)
    if last_record is None:
        return 0
    replace(records, last_record, end=now())
    save(records=records)


def remove_last():
    """remove previous activity"""
    meta, projects, records = load()
    project = require_current_project(meta, projects)
    last_record = get_last_record(project, records)
    if last_record is None:
        return 0
    records.remove(last_record)
    save(records=records)


def status():
    """print project and current situation"""
    meta, projects, records = load()
    project = get_current_project(meta, projects)
    if not project:
        print("Current project not set")
        return 0
    last_record = get_last_record(project, records)
    print("Currently working on project {0}".format(project.name))
    print("Last record {0}".format(last_record))


def log():
    """print ordered work log"""
    meta, projects, records = load()
    project = require_current_project(meta, projects)
    records = sorted(filter_project_records(project, records),
                     key=lambda r: r.start)
    row_format = "{0:15}{1:20}{2:20}{3:15}"
    print(row_format.format("PHASE", "START", "END", "DELTA"))
    for record in records:
        start = record.start.strftime("%Y-%m-%d %H:%M") if record.start else ""
        end = record.end.strftime("%Y-%m-%d %H:%M") if record.end else ""
        delta = delta_str((record.end or now()) - record.start)
        print(row_format.format(record.phase, start, end, delta))


def usage():
    print("Usage: {0} [start|end|project|status|log|remove-last|usage]".format(
        sys.argv[0]))
    return 1


def main():
    commands = {
        "start": start,
        "end": end,
        "project": project,
        "status": status,
        "log": log,
        "remove-last": remove_last,
        "usage": usage,
    }
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        return usage()
    return commands[sys.argv[1]](*sys.argv[2:]) or 0


if __name__ == "__main__":
    sys.exit(main())
