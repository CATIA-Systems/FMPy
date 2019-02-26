def generate_result_tables(repo_dir, data_dir):
    """ Generate the cross-check result tables """

    import os
    import csv
    from fmpy.cross_check import get_vendor_ids

    combinations = []  # all permutations of FMI version, type and platform

    for fmi_version in ['1.0', '2.0']:
        for fmi_type in ['cs', 'me']:
            for platform in ['c-code', 'darwin64', 'linux32', 'linux64', 'win32', 'win64']:
                combinations.append((fmi_version, fmi_type, platform))

    tools_csv = os.path.join(data_dir, 'tools.csv')

    vendors = get_vendor_ids(tools_csv)

    tools = {}  # tool_id -> tool_name

    for tool_infos in vendors.values():
        for tool_id, tool_name in tool_infos:
            tools[tool_id] = tool_name

    def split_path(path):

        segments = []

        while True:
            path, segment = os.path.split(path)
            if not segment:
                break
            segments.insert(0, segment)

        return segments

    def collect_results():

        results = []

        vendor_repo = os.path.join(repo_dir, 'results')

        for root, dirs, files in os.walk(vendor_repo):

            if 'passed' not in files:
                continue  # ignore

            segments = split_path(root)

            fmi_version, fmi_type, platform, _, _, exporting_tool_name, exporting_tool_version, model_name = segments[-8:]

            not_compliant_file = os.path.join(repo_dir, 'fmus', fmi_version, fmi_type, platform, exporting_tool_name, exporting_tool_version, model_name, 'notCompliantWithLatestRules')

            if os.path.isfile(not_compliant_file):
                continue  # ignore

            results.append(segments[-8:])

        return results

    def build_matrix(results, fmi_version, fmi_type, platform):
        """ Build the result matrix for an FMI version, type and platform """

        importing_tools = set()
        exporting_tools = set()

        filtered = []

        # get the tools
        for fmi_version_, fmi_type_, platform_, importing_tool_name, importing_tool_version, exporting_tool_name, exporting_tool_version, model_name in results:

            if fmi_version_ != fmi_version or fmi_type_ != fmi_type or platform_ != platform:
                continue

            importing_tools.add(importing_tool_name)
            exporting_tools.add(exporting_tool_name)

            filtered.append((importing_tool_name, importing_tool_version, exporting_tool_name, exporting_tool_version, model_name))

        # build matrix
        importing_tools = sorted(importing_tools, key=lambda s: s.lower())
        exporting_tools = sorted(exporting_tools, key=lambda s: s.lower())

        matrix = []

        for importing_tool in importing_tools:
            row = []
            for exporting_tool in exporting_tools:
                count = 0
                for r in filtered:
                    if r[0] == importing_tool and r[2] == exporting_tool:
                        count += 1
                row.append(count)
            matrix.append(row)

        return importing_tools, exporting_tools, matrix

    results = collect_results()

    # filter tool IDs
    results = [r for r in results if r[3] in tools and r[5] in tools]

    matrices = {}

    for combination in combinations:
        matrices[combination] = build_matrix(results, *combination)

    for fmi_version, fmi_type, platform in combinations:

        importing_tools, exporting_tools, matrix = matrices[(fmi_version, fmi_type, platform)]

        importing_tools = [tools[tool_id] for tool_id in importing_tools]
        exporting_tools = [tools[tool_id] for tool_id in exporting_tools]

        csv_filename = 'fmi1' if fmi_version == '1.0' else 'fmi2'
        csv_filename += '-'
        csv_filename += fmi_type
        csv_filename += '-'
        csv_filename += platform + '.csv'

        with open(os.path.join(data_dir, 'cross-check', csv_filename), 'w') as f:
            f.write(','.join([''] + exporting_tools) + '\n')
            for importing_tool, row in zip(importing_tools, matrix):
                f.write(','.join([importing_tool] + list(map(str, row))) + '\n')

    participants = set()

    # generate the tools file with cross-check results
    export_passed = {}
    import_passed = {}

    for fmi_version, fmi_type, platform, importing_tool_name, importing_tool_version, exporting_tool_name, exporting_tool_version, model_name in results:

        key = (exporting_tool_name, fmi_version, fmi_type)

        participants.add(exporting_tool_name)
        participants.add(importing_tool_name)

        if key not in export_passed:
            export_passed[key] = {}

        if importing_tool_name not in export_passed[key]:
            export_passed[key][importing_tool_name] = {model_name}
        else:
            export_passed[key][importing_tool_name].add(model_name)

        key = (importing_tool_name, fmi_version, fmi_type)

        if key not in import_passed:
            import_passed[key] = {}

        if exporting_tool_name not in import_passed[key]:
            import_passed[key][exporting_tool_name] = {model_name}
        else:
            import_passed[key][exporting_tool_name].add(model_name)

    # aggregate the results
    participants = sorted(participants, key=lambda s: s.lower())

    rows = [participants]

    def check_passed(key, d):
        cnt = 0
        for vendor, models in d.get(key, {}).items():
            if len(models) >= 3:
                cnt += 1
        return cnt >= 3

    for results in [export_passed, import_passed]:

        for i, c in enumerate([('cs', '1.0'), ('cs', '2.0'), ('me', '1.0'), ('me', '2.0')]):

            fmi_type, fmi_version = c
            row = []

            for tool_id in participants:
                key = (tool_id, fmi_version, fmi_type)
                row.append('passed' if check_passed(key, results) else '')

            rows.append(row)

    with open(os.path.join(data_dir, 'cross-check', 'result.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)


if __name__ is '__main__':

    import argparse

    parser = argparse.ArgumentParser(description="Generate the cross-check result tables")

    parser.add_argument('xc_repo_dir', help="Cloned cross-check repository")
    parser.add_argument('data_dir', help="_data directory in the fmi-standard.org repository")

    args = parser.parse_args()

    generate_result_tables(repo_dir=args.xc_repo_dir, data_dir=args.data_dir)
