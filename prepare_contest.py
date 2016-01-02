#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from optparse import *
import os.path
import re
import subprocess
import sys
import time
import urllib.request
import shutil
import json

from lxml import etree

CODEFORCES_URL = 'http://codeforces.com'
EPS = 1e-6

"""
./prepare_contest.py -n upsolving -u https://official.contest.yandex.com/ukrcamp2015a/contest/1517/problems/ -c ukrcamp2015/cookie.json -j Y

"""

def add_options():
    usage = '%prog [options] [source code]'
    parser = OptionParser(usage=usage)
    parser.add_option('-j', '--judge', dest='online_judge', help='Online Judge with problem/contest.')
    parser.add_option('-u', '--contest_url', dest='contest_url', help="Download the specific contest. \
                                                                    If the PROBLEM_ID isn't specific, \
                                                                    then download all problems in the contest.")
    parser.add_option('-c', '--cookies', dest='cookies_path', help="Cookies to connect server")
    parser.add_option('-n', '--contest_name', help="Verbose contest name")

    return parser.parse_args()

def node_to_string(node):
    return ''.join([node.text] + [etree.tostring(c).decode('utf-8') for c in node.getchildren()])

class CodeForces():
    def __init__(self):
        self.url = 'http://codeforces.com'
        self.name = 'codeforces'
        self.opener = urllib.request.build_opener()

    def get_page_tree(self, path):
        page_url = urllib.parse.urljoin(self.url, path)
        print("Downloading...", page_url)
        page_content = self.opener.open(page_url).read().decode('utf-8')
        return etree.HTML(page_content)

    def download_contest(self, contest_path):
        tree = self.get_page_tree(contest_path)

        problems = []
        for i in tree.xpath(".//table[contains(@class, 'problems')]//td[contains(@class, 'id')]/a"):
            problems.append(self.download_problem(i.attrib['href']))
        return problems

    def download_problem(self, problem_path):
        tree = self.get_page_tree(problem_path)

        title = tree.xpath('.//div[contains(@class, "problem-statement")]/div/div[contains(@class, "title")]')[0].text

        tests = []
        for (input_node, answer_node) in zip(tree.xpath('.//div[contains(@class, "input")]/pre'),
                                             tree.xpath('.//div[contains(@class, "output")]/pre')):
            input = node_to_string(input_node).replace('<br/>', '\n')
            answer = node_to_string(answer_node).replace('<br/>', '\n')
            tests.append( (input, answer) )

        return (title, tests)

class Yandex():
    def __init__(self, url=None, cookies=None):
        self.url = 'http://official.contest.yandex.com'
        self.name = 'yandex'
        self.opener = urllib.request.build_opener()
        if cookies is not None:
            self.opener.addheaders.append(('Cookie', cookies))

    def get_page_tree(self, path):
        page_url = urllib.parse.urljoin(self.url, path)
        print("Downloading...", page_url)
        page_content = self.opener.open(page_url).read().decode('utf-8')
        return etree.HTML(page_content)

    def download_contest(self, contest_path):
        tree = self.get_page_tree(contest_path)

        div_class = "tabs-menu tabs-menu_theme_normal tabs-menu_layout_vert "\
                    "tabs-menu_size_m tabs-menu_role_problems inline-block i-bem"

        problems = []
        for i in tree.xpath(".//div[contains(@class, '" + div_class + "')]/a"):
            problems.append( ( i.getchildren()[0].text, self.download_problem(i.attrib['href']) ) )

        return problems

    def download_problem(self, problem_path):
        tree = self.get_page_tree(problem_path)

        tests = []
        for sample in tree.xpath(".//table[contains(@class, 'sample-tests')]/tbody/tr"):
            input_node, output_node = sample.findall("td/pre")
            tests.append( (input_node.text, output_node.text) )

        return tests

def prepare_dir(contest_folder, name, tests):
    name = name.replace(' ', '_').replace('"', '').replace('.', '').replace('\\', '').replace('/', '').replace(',', '')
    problem_folder = os.path.join(contest_folder, name)
    print(problem_folder)
    if not os.path.exists(problem_folder):
        os.makedirs(problem_folder)

    filename = os.path.join(problem_folder, "main.xml")
    with open(filename, 'w') as fd:
        for input, answer in tests:
            fd.write('<input>\n')
            fd.write(input)
            if input[-1] != '\n': fd.write('\n')
            fd.write('\n</input>\n')
            fd.write('<answer>\n')
            fd.write(answer)
            if answer[-1] != '\n': fd.write('\n')
            fd.write('\n</answer>\n')

    shutil.copy("exm.cpp", os.path.join(problem_folder, "main.cpp"))
    shutil.copy("cf.py", problem_folder)
    shutil.copy("conf.py", problem_folder)


def main():
    global options
    (options, args) = add_options()


    contest_url = urllib.parse.urlparse(options.contest_url)
    print(contest_url)
    online_judge_url = contest_url.netloc
    contest_path = contest_url.path

    if options.online_judge == "codeforces" or options.online_judge == "CF":
        online_judge = CodeForces()
    elif options.online_judge == "yandex" or options.online_judge == "Y":
        cookies_json = json.load( open(options.cookies_path, "r") )
        cookies = "; ".join([c["name"] + "=" + c["value"] for c in cookies_json])

        online_judge = Yandex(url=online_judge_url, cookies=cookies)
    else:
        print("Specify OJ")
        sys.exit(1)

    contest_folder = os.path.join('.', online_judge.name, options.contest_name)
    src_folder = os.path.join(contest_folder, 'src')
    test_folder = os.path.join(contest_folder, 'test')
    bin_folder = os.path.join(contest_folder, 'bin')

    if not os.path.exists(contest_folder):
        os.makedirs(contest_folder)

    print(contest_folder, src_folder, test_folder, bin_folder)

    problems = online_judge.download_contest(contest_path)

    print(problems)

    for name, tests in problems:
        prepare_dir(contest_folder, name, tests)

if __name__ == '__main__':
    main()
