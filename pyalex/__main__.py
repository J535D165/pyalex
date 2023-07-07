import argparse
import sys
from pprint import pprint

import yaml

from pyalex import Authors
from pyalex import Concepts
from pyalex import Funders
from pyalex import Institutions
from pyalex import Publishers
from pyalex import Sources
from pyalex import Works
from pyalex.api import QueryError


def _parse_nested_arguments(s):

    k, v = s.split("=")

    if "." in k:
        k_split = k.split(".")
        k_dict = {k_split[-1]: v}
        for p in k_split[1::-1]:
            k_dict = {p: k_dict}
        return k_dict

    return {k: v}


def _cli_to_api(resource_class, args):
    """Convert CLI arguments to PyAlex API calls."""

    if args.id:
        args.id = args.id[0]
        r = resource_class()[args.id]
        if args.output_type == "yaml":
            yaml.dump(dict(r), sys.stdout, default_flow_style=False)
        else:
            pprint(r)
        return

    resource = resource_class()

    if args.filter:
        for f in args.filter:
            kwargs = _parse_nested_arguments(f)
            resource.filter(**kwargs)

    if args.select:
        resource.select(args.select)

    if args.search_filter:
        for f in args.search_filter:
            kwargs = _parse_nested_arguments(f)
            resource.search_filter(**kwargs)

    if args.sort:
        for f in args.sort:
            kwargs = _parse_nested_arguments(f)
            resource.sort(**kwargs)

    if args.sample:
        resource.sample(args.sample)

    if args.search:
        resource.search(args.search)

    try:
        r = resource.get(per_page=args.per_page)
    except QueryError as e:
        print("Error:", e)
        sys.exit(1)

    if args.output_type == "yaml":
        for i in r:
            print("---")
            yaml.dump(dict(i), sys.stdout, default_flow_style=False)
    else:
        pprint(r)


def main():

    parser = argparse.ArgumentParser(prog="pyalex", description="OpenAlex Interface")
    subparsers = parser.add_subparsers(help="OpenAlex resources")

    openalex_actions_parser = argparse.ArgumentParser(add_help=False)
    openalex_actions_parser.add_argument("id", type=str, nargs="*", help="OpenAlex ID")
    openalex_actions_parser.add_argument(
        "--filter", type=str, action="append", help="Filter records"
    )
    openalex_actions_parser.add_argument(
        "--select", type=str, action="append", help="Select fields"
    )
    openalex_actions_parser.add_argument(
        "--search_filter", type=str, action="append", help="Search filter fields"
    )
    openalex_actions_parser.add_argument(
        "--sort", type=str, action="append", help="Sort results by field"
    )
    openalex_actions_parser.add_argument(
        "--sample", type=int, help="Sample number of results"
    )
    openalex_actions_parser.add_argument(
        "--search", type=str, action="append", help="Search for records"
    )
    openalex_actions_parser.add_argument(
        "--per-page", type=int, default=None, help="Number of results per page"
    )
    openalex_actions_parser.add_argument(
        "--output-type",
        "-o",
        type=str,
        default="yaml",
        choices=["yaml", "json"],
        help="Output type. Default yaml.",
    )

    # subparsers for each OpenAlex resource
    for subparser in [
        Works,
        Authors,
        Sources,
        Institutions,
        Concepts,
        Funders,
        Publishers,
    ]:
        subparser_name = subparser.__name__.lower()
        parser_subparser = subparsers.add_parser(
            subparser_name,
            parents=[openalex_actions_parser],
            help=f"Retrieve OpenAlex {subparser.__name__}",
        )
        parser_subparser.set_defaults(func=_cli_to_api, resource_class=subparser)

    # parse the arguments
    args = parser.parse_args(sys.argv[1:])

    # parse the arguments into a PyAlex API call
    args.func(args.resource_class, args)


if __name__ == "__main__":
    main()
