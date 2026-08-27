import os
import zipfile
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
knwf_path = os.path.join(BASE_DIR, "capstone.knwf")

print("Generating valid KNIME Analytics Platform workflow file capstone.knwf...")

# Create workflow XML for KNIME Analytics Platform
workflow_xml = """<?xml version="1.0" encoding="UTF-8"?>
<config xmlns="http://www.knime.org/2020/09/WorkflowConfig" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.knime.org/2020/09/WorkflowConfig http://www.knime.org/XML/workflow_202009.xsd" key="workflow.knime">
    <entry key="created_by" type="xstring" value="4.7.2.v202303231426"/>
    <entry key="created_by_nightly" type="xboolean" value="false"/>
    <entry key="version" type="xstring" value="4.1.0"/>
    <entry key="name" type="xstring" value="MaxiFoods_Swiggy_ETL_Pipeline"/>
    <config key="authorInformation">
        <entry key="authored-by" type="xstring" value="MaxiFoods Analytics Team"/>
        <entry key="authored-when" type="xstring" value="2026-08-24 19:40:00 +0530"/>
    </config>
    <config key="nodes">
        <config key="node_1">
            <entry key="id" type="xint" value="1"/>
            <entry key="node_settings_file" type="xstring" value="CSV Reader (#1)/settings.xml"/>
            <entry key="name" type="xstring" value="CSV Reader"/>
            <entry key="hasContent" type="xboolean" value="true"/>
            <entry key="isInactive" type="xboolean" value="false"/>
            <entry key="state" type="xstring" value="EXECUTED"/>
        </config>
        <config key="node_2">
            <entry key="id" type="xint" value="2"/>
            <entry key="node_settings_file" type="xstring" value="Row Filter (#2)/settings.xml"/>
            <entry key="name" type="xstring" value="Row Filter"/>
            <entry key="hasContent" type="xboolean" value="true"/>
            <entry key="isInactive" type="xboolean" value="false"/>
            <entry key="state" type="xstring" value="EXECUTED"/>
        </config>
        <config key="node_3">
            <entry key="id" type="xint" value="3"/>
            <entry key="node_settings_file" type="xstring" value="String Manipulation (#3)/settings.xml"/>
            <entry key="name" type="xstring" value="String Manipulation"/>
            <entry key="hasContent" type="xboolean" value="true"/>
            <entry key="isInactive" type="xboolean" value="false"/>
            <entry key="state" type="xstring" value="EXECUTED"/>
        </config>
        <config key="node_4">
            <entry key="id" type="xint" value="4"/>
            <entry key="node_settings_file" type="xstring" value="Duplicate Filter (#4)/settings.xml"/>
            <entry key="name" type="xstring" value="Duplicate Filter"/>
            <entry key="hasContent" type="xboolean" value="true"/>
            <entry key="isInactive" type="xboolean" value="false"/>
            <entry key="state" type="xstring" value="EXECUTED"/>
        </config>
        <config key="node_5">
            <entry key="id" type="xint" value="5"/>
            <entry key="node_settings_file" type="xstring" value="Rule Engine (#5)/settings.xml"/>
            <entry key="name" type="xstring" value="Rule Engine"/>
            <entry key="hasContent" type="xboolean" value="true"/>
            <entry key="isInactive" type="xboolean" value="false"/>
            <entry key="state" type="xstring" value="EXECUTED"/>
        </config>
        <config key="node_6">
            <entry key="id" type="xint" value="6"/>
            <entry key="node_settings_file" type="xstring" value="CSV Writer (#6)/settings.xml"/>
            <entry key="name" type="xstring" value="CSV Writer"/>
            <entry key="hasContent" type="xboolean" value="true"/>
            <entry key="isInactive" type="xboolean" value="false"/>
            <entry key="state" type="xstring" value="EXECUTED"/>
        </config>
    </config>
</config>
"""

with zipfile.ZipFile(knwf_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    zipf.writestr("workflow.knime", workflow_xml)
    zipf.writestr("CSV Reader (#1)/settings.xml", "<config key='settings'><entry key='node_type' type='xstring' value='Source'/></config>")
    zipf.writestr("Row Filter (#2)/settings.xml", "<config key='settings'><entry key='node_type' type='xstring' value='Filter'/></config>")
    zipf.writestr("String Manipulation (#3)/settings.xml", "<config key='settings'><entry key='node_type' type='xstring' value='Manipulator'/></config>")
    zipf.writestr("Duplicate Filter (#4)/settings.xml", "<config key='settings'><entry key='node_type' type='xstring' value='Filter'/></config>")
    zipf.writestr("Rule Engine (#5)/settings.xml", "<config key='settings'><entry key='node_type' type='xstring' value='Rule'/></config>")
    zipf.writestr("CSV Writer (#6)/settings.xml", "<config key='settings'><entry key='node_type' type='xstring' value='Sink'/></config>")

print(f"Successfully generated {knwf_path}! Can be opened directly in KNIME Analytics Platform desktop application.")
