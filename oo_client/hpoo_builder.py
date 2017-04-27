import StringIO
import xml.etree.ElementTree as ET
import ConfigParser
import os
import oo_client.errors as errors
from subprocess import check_call
from subprocess import call
from subprocess import check_output
import logging


class ContentBuilder(object):
    def __init__(self, path_to_content, svn_path=""):
        self.path = path_to_content
        self.config = self.read_props()
        self.cp_name = self.config.get('cp', 'content.pack.name')
        self.log = logging.getLogger(self.__class__.__name__)
        self.svn_path = svn_path

    def run_build(self, release=False, version=None, system_props=True,
                  system_accts=True, system_accts_passwds=False,
                  branch="trunk"):
        os.chdir(self.path)
        if release:
            if not version:
                version = self.config.get('cp', 'content.pack.version')
                version = version.replace('-SNAPSHOT', '')
            self.check_version_doesnt_exist(version)
            cp_name = '{0}-cp-{1}.jar'.format(self.cp_name, version)
            self.set_cp_version(version)
            if branch == 'trunk':
                self.log.info("Creating release branch")
                check_call(['svn', 'copy', '^{0}/trunk'.format(self.svn_path),
                            '^{0}/branches/'
                            'releases/{1}-{2}'.format(self.svn_path,
                                                      self.cp_name,
                                                      version),
                            '-m', 'Creating release branch'])
            self.log.info("Tagging release")
            check_call(['svn', 'copy',
                        '^{0}/branches/releases/{1}-{2}'.format(self.svn_path,
                                                                self.cp_name,
                                                                version),
                        '^{0}/tags/releases/{1}-{2}'.format(self.svn_path,
                                                            self.cp_name,
                                                            version),
                        '-m', 'Creating release branch'])
        else:
            self.rev = check_output('svnversion').strip()
            version = self.config.get('cp', 'content.pack.version')
            version = version.replace('-SNAPSHOT', '')
            cp_name = '{0}-cp-{1}-{2}-SNAPSHOT.jar'.format(self.cp_name,
                                                           version,
                                                           self.rev)
        os.mkdir('{0}/Lib'.format(self.path))
        self.log.info("Creating content pack {0}".format(cp_name))
        cp_path = "./target/{0}".format(cp_name)
        check_call(['jar', 'cf', cp_path, '-C', self.path, '.'])
        os.rmdir('{0}/Lib'.format(self.path))
        if release:
            version = self.increase_version(version)
            self.set_cp_version("{0}-SNAPSHOT".format(version))
            check_call(['svn', 'commit',
                        '-m', 'Updating contentpack.properties'])
        self.log.info("Done")

    def increase_version(self, version, increment=1):
        version = version.split('.')
        minor = int(version[-1])
        minor = minor + increment
        version[-1] = str(minor)
        ret = '.'.join(version)
        return ret

    def check_version_doesnt_exist(self, version):
        self.log.info("Checking release doesn't already exist in SVN")
        ret = call(['svn', 'info',
                    '^{0}/tags/releases/{1}-{2}'.format(self.svn_path,
                                                        self.cp_name,
                                                        version)])
        if ret == 0:
            raise errors.ReleaseAlreadyExists(version)
        return True

    def set_cp_version(self, version):
        self.log.info('Updating contentpack.properties version to'
                      ' {0}'.format(version))
        if self.pom_exists():
            self.set_pom_version(version)
        self.set_config_version(version)

    def read_props(self):
        prop_file = open('{0}/contentpack.properties'.format(self.path))
        config = StringIO.StringIO()
        config.write('[cp]\n')
        config.write(prop_file.read())
        config.seek(0, os.SEEK_SET)
        cp = ConfigParser.ConfigParser()
        cp.readfp(config)
        return cp

    def set_pom_version(self, version):
        pom_path = '{0}/pom.xml'.format(self.path)
        tree = ET.parse(pom_path)
        root = tree.getroot()
        cur_ver = root.find('./{http://maven.apache.org/POM/4.0.0}version')
        cur_ver.text = version
        tree.write(pom_path, xml_declaration=True,
                   encoding='utf-8', method="xml",
                   default_namespace='http://maven.apache.org/POM/4.0.0')

    def set_config_version(self, version):
        self.config.set('cp', 'content.pack.version', version)
        prop_file = '{0}/contentpack.properties'.format(self.path)
        with open(prop_file, 'w') as cf:
            self.config.write(cf)
        self.remove_whitespace_from_assignments()

    def pom_exists(self):
        return os.path.isfile('{0}/pom.xml'.format(self.path))

    def remove_whitespace_from_assignments(self):
        separator = "="
        config_path = '{0}/contentpack.properties'.format(self.path)
        lines = file(config_path).readlines()
        fp = open(config_path, "w")
        for line in lines:
            line = line.strip()
            if not line.startswith("#") and separator in line:
                assignment = line.split(separator, 1)
                assignment = map(str.strip, assignment)
                fp.write("%s%s%s\n" % (assignment[0],
                                       separator,
                                       assignment[1]))
            elif line.startswith('['):
                continue
            else:
                fp.write(line + "\n")
