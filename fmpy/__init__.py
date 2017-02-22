import os

from lxml import etree
from ctypes import *
from itertools import combinations

FMI2_SCHEMA = '<?xml version="1.0" encoding="UTF-8" ?><xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified" attributeFormDefault="unqualified"><xs:complexType name="fmi2ScalarVariable"><xs:annotation><xs:documentation>Properties of a scalar variable</xs:documentation></xs:annotation><xs:sequence><xs:choice><xs:element name="Real"><xs:complexType><xs:attribute name="declaredType" type="xs:normalizedString"><xs:annotation><xs:documentation>If present, name of type defined with TypeDefinitions / SimpleType providing defaults.</xs:documentation></xs:annotation></xs:attribute><xs:attributeGroup ref="fmi2RealAttributes"></xs:attributeGroup><xs:attribute name="start" type="xs:double"><xs:annotation><xs:documentation>Value before initialization, if initial=exact or approx.max &amp;gt;= start &amp;gt;= min required</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="derivative" type="xs:unsignedInt"><xs:annotation><xs:documentation>If present, this variable is the derivative of variable with ScalarVariable index &amp;quot;derivative&amp;quot;.</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="reinit" type="xs:boolean" use="optional" default="false"><xs:annotation><xs:documentation>Only for ModelExchange and if variable is a continuous-time state:If true, state can be reinitialized at an event by the FMUIf false, state will never be reinitialized at an event by the FMU</xs:documentation></xs:annotation></xs:attribute></xs:complexType></xs:element><xs:element name="Integer"><xs:complexType><xs:attribute name="declaredType" type="xs:normalizedString"><xs:annotation><xs:documentation>If present, name of type defined with TypeDefinitions / SimpleType providing defaults.</xs:documentation></xs:annotation></xs:attribute><xs:attributeGroup ref="fmi2IntegerAttributes"></xs:attributeGroup><xs:attribute name="start" type="xs:int"><xs:annotation><xs:documentation>Value before initialization, if initial=exact or approx.max &amp;gt;= start &amp;gt;= min required</xs:documentation></xs:annotation></xs:attribute></xs:complexType></xs:element><xs:element name="Boolean"><xs:complexType><xs:attribute name="declaredType" type="xs:normalizedString"><xs:annotation><xs:documentation>If present, name of type defined with TypeDefinitions / SimpleType providing defaults.</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="start" type="xs:boolean"><xs:annotation><xs:documentation>Value before initialization, if initial=exact or approx</xs:documentation></xs:annotation></xs:attribute></xs:complexType></xs:element><xs:element name="String"><xs:complexType><xs:attribute name="declaredType" type="xs:normalizedString"><xs:annotation><xs:documentation>If present, name of type defined with TypeDefinitions / SimpleType providing defaults.</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="start" type="xs:string"><xs:annotation><xs:documentation>Value before initialization, if initial=exact or approx</xs:documentation></xs:annotation></xs:attribute></xs:complexType></xs:element><xs:element name="Enumeration"><xs:complexType><xs:attribute name="declaredType" type="xs:normalizedString" use="required"><xs:annotation><xs:documentation>Name of type defined with TypeDefinitions / SimpleType</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="quantity" type="xs:normalizedString"></xs:attribute><xs:attribute name="min" type="xs:int"></xs:attribute><xs:attribute name="max" type="xs:int"><xs:annotation><xs:documentation>max &amp;gt;= min required</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="start" type="xs:int"><xs:annotation><xs:documentation>Value before initialization, if initial=exact or approx.max &amp;gt;= start &amp;gt;= min required</xs:documentation></xs:annotation></xs:attribute></xs:complexType></xs:element></xs:choice><xs:element name="Annotations" type="fmi2Annotation" minOccurs="0"><xs:annotation><xs:documentation>Additional data of the scalar variable, e.g., for the dialog menu or the graphical layout</xs:documentation></xs:annotation></xs:element></xs:sequence><xs:attribute name="name" type="xs:normalizedString" use="required"><xs:annotation><xs:documentation>Identifier of variable, e.g. &amp;quot;a.b.mod[3,4].&amp;quot;#123&amp;quot;.c&amp;quot;. &amp;quot;name&amp;quot; must be unique with respect to all other elements of the ModelVariables list</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="valueReference" type="xs:unsignedInt" use="required"><xs:annotation><xs:documentation>Identifier for variable value in FMI2 function calls (not necessarily unique with respect to all variables)</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="description" type="xs:string"></xs:attribute><xs:attribute name="causality" default="local"><xs:annotation><xs:documentation>parameter: independent parametercalculatedParameter: calculated parameterinput/output: can be used in connectionslocal: variable calculated from other variablesindependent: independent variable (usually time)</xs:documentation></xs:annotation><xs:simpleType><xs:restriction base="xs:normalizedString"><xs:enumeration value="parameter"></xs:enumeration><xs:enumeration value="calculatedParameter"></xs:enumeration><xs:enumeration value="input"></xs:enumeration><xs:enumeration value="output"></xs:enumeration><xs:enumeration value="local"></xs:enumeration><xs:enumeration value="independent"></xs:enumeration></xs:restriction></xs:simpleType></xs:attribute><xs:attribute name="variability" default="continuous"><xs:annotation><xs:documentation>constant: value never changesfixed: value fixed after initializationtunable: value constant between external eventsdiscrete: value constant between internal eventscontinuous: no restriction on value changes</xs:documentation></xs:annotation><xs:simpleType><xs:restriction base="xs:normalizedString"><xs:enumeration value="constant"></xs:enumeration><xs:enumeration value="fixed"></xs:enumeration><xs:enumeration value="tunable"></xs:enumeration><xs:enumeration value="discrete"></xs:enumeration><xs:enumeration value="continuous"></xs:enumeration></xs:restriction></xs:simpleType></xs:attribute><xs:attribute name="initial"><xs:annotation><xs:documentation>exact: initialized with start valueapprox: iteration variable that starts with start valuecalculated: calculated from other variables.If not provided, initial is deduced from causality and variability (details see specification)</xs:documentation></xs:annotation><xs:simpleType><xs:restriction base="xs:normalizedString"><xs:enumeration value="exact"></xs:enumeration><xs:enumeration value="approx"></xs:enumeration><xs:enumeration value="calculated"></xs:enumeration></xs:restriction></xs:simpleType></xs:attribute><xs:attribute name="canHandleMultipleSetPerTimeInstant" type="xs:boolean"><xs:annotation><xs:documentation>Only for ModelExchange and only for variables with variability = &amp;quot;input&amp;quot;:If present with value = false, then only one fmi2SetXXX call is allowed at one super dense time instant. In other words, this input is not allowed to appear in an algebraic loop.</xs:documentation></xs:annotation></xs:attribute></xs:complexType><xs:complexType name="fmi2VariableDependency"><xs:sequence maxOccurs="unbounded"><xs:element name="Unknown"><xs:annotation><xs:documentation>Dependency of scalar Unknown from Knownsin Continuous-Time and Event Mode (ModelExchange),and at Communication Points (CoSimulation): Unknown=f(Known_1, Known_2, ...).The Knowns are &amp;quot;inputs&amp;quot;, &amp;quot;continuous states&amp;quot; and&amp;quot;independent variable&amp;quot; (usually time)&amp;quot;.</xs:documentation></xs:annotation><xs:complexType><xs:attribute name="index" type="xs:unsignedInt" use="required"><xs:annotation><xs:documentation>ScalarVariable index of Unknown</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="dependencies"><xs:annotation><xs:documentation>Defines the dependency of the Unknown (directly or indirectly via auxiliary variables) on the Knowns in Continuous-Time and Event Mode (ModelExchange) and at Communication Points (CoSimulation). If not present, it must be assumed that the Unknown depends on all Knowns. If present as empty list, the Unknown depends on none of the Knowns. Otherwise the Unknown depends on the Knowns defined by the given ScalarVariable indices. The indices are ordered according to size, starting with the smallest index.</xs:documentation></xs:annotation><xs:simpleType><xs:list itemType="xs:unsignedInt"></xs:list></xs:simpleType></xs:attribute><xs:attribute name="dependenciesKind"><xs:annotation><xs:documentation>If not present, it must be assumed that the Unknown depends on the Knowns without a particular structure. Otherwise, the corresponding Known v enters the equation as:= &amp;quot;dependent&amp;quot;: no particular structure, f(v)= &amp;quot;constant&amp;quot; : constant factor, c*v (only for Real variablse)= &amp;quot;fixed&amp;quot; : fixed factor, p*v (only for Real variables)= &amp;quot;tunable&amp;quot; : tunable factor, p*v (only for Real variables)= &amp;quot;discrete&amp;quot; : discrete factor, d*v (only for Real variables)If &amp;quot;dependenciesKind&amp;quot; is present, &amp;quot;dependencies&amp;quot; must be present and must have the same number of list elements.</xs:documentation></xs:annotation><xs:simpleType><xs:list><xs:simpleType><xs:restriction base="xs:normalizedString"><xs:enumeration value="dependent"></xs:enumeration><xs:enumeration value="constant"></xs:enumeration><xs:enumeration value="fixed"></xs:enumeration><xs:enumeration value="tunable"></xs:enumeration><xs:enumeration value="discrete"></xs:enumeration></xs:restriction></xs:simpleType></xs:list></xs:simpleType></xs:attribute></xs:complexType></xs:element></xs:sequence></xs:complexType><xs:complexType name="fmi2Unit"><xs:annotation><xs:documentation>Unit definition (with respect to SI base units) and default display units</xs:documentation></xs:annotation><xs:sequence><xs:element name="BaseUnit" minOccurs="0"><xs:annotation><xs:documentation>BaseUnit_value = factor*Unit_value + offset</xs:documentation></xs:annotation><xs:complexType><xs:attribute name="kg" type="xs:int" default="0"><xs:annotation><xs:documentation>Exponent of SI base unit &amp;quot;kg&amp;quot;</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="m" type="xs:int" default="0"><xs:annotation><xs:documentation>Exponent of SI base unit &amp;quot;m&amp;quot;</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="s" type="xs:int" default="0"><xs:annotation><xs:documentation>Exponent of SI base unit &amp;quot;s&amp;quot;</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="A" type="xs:int" default="0"><xs:annotation><xs:documentation>Exponent of SI base unit &amp;quot;A&amp;quot;</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="K" type="xs:int" default="0"><xs:annotation><xs:documentation>Exponent of SI base unit &amp;quot;K&amp;quot;</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="mol" type="xs:int" default="0"><xs:annotation><xs:documentation>Exponent of SI base unit &amp;quot;mol&amp;quot;</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="cd" type="xs:int" default="0"><xs:annotation><xs:documentation>Exponent of SI base unit &amp;quot;cd&amp;quot;</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="rad" type="xs:int" default="0"><xs:annotation><xs:documentation>Exponent of SI derived unit &amp;quot;rad&amp;quot;</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="factor" type="xs:double" default="1"></xs:attribute><xs:attribute name="offset" type="xs:double" default="0"></xs:attribute></xs:complexType></xs:element><xs:sequence minOccurs="0" maxOccurs="unbounded"><xs:element name="DisplayUnit"><xs:annotation><xs:documentation>DisplayUnit_value = factor*Unit_value + offset</xs:documentation></xs:annotation><xs:complexType><xs:attribute name="name" type="xs:normalizedString" use="required"><xs:annotation><xs:documentation><Unit name="rad"></Unit><DisplayUnit name="deg" factor="57.29..."></DisplayUnit></xs:documentation></xs:annotation></xs:attribute><xs:attribute name="factor" type="xs:double" default="1"></xs:attribute><xs:attribute name="offset" type="xs:double" default="0"></xs:attribute></xs:complexType></xs:element></xs:sequence></xs:sequence><xs:attribute name="name" type="xs:normalizedString" use="required"><xs:annotation><xs:documentation>Name of Unit element, e.g. &amp;quot;N.m&amp;quot;, &amp;quot;Nm&amp;quot;, &amp;quot;%/s&amp;quot;. &amp;quot;name&amp;quot; must be unique will respect to all other elements of the UnitDefinitions list. The variable values of fmi2SetXXX and fmi2GetXXX are with respect to this unit.</xs:documentation></xs:annotation></xs:attribute></xs:complexType><xs:complexType name="fmi2SimpleType"><xs:annotation><xs:documentation>Type attributes of a scalar variable</xs:documentation></xs:annotation><xs:sequence><xs:choice><xs:element name="Real"><xs:complexType><xs:attributeGroup ref="fmi2RealAttributes"></xs:attributeGroup></xs:complexType></xs:element><xs:element name="Integer"><xs:complexType><xs:attributeGroup ref="fmi2IntegerAttributes"></xs:attributeGroup></xs:complexType></xs:element><xs:element name="Boolean"></xs:element><xs:element name="String"></xs:element><xs:element name="Enumeration"><xs:complexType><xs:sequence maxOccurs="unbounded"><xs:element name="Item"><xs:complexType><xs:attribute name="name" type="xs:normalizedString" use="required"></xs:attribute><xs:attribute name="value" type="xs:int" use="required"><xs:annotation><xs:documentation>Must be a unique number in the same enumeration</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="description" type="xs:string"></xs:attribute></xs:complexType></xs:element></xs:sequence><xs:attribute name="quantity" type="xs:normalizedString"></xs:attribute></xs:complexType></xs:element></xs:choice></xs:sequence><xs:attribute name="name" type="xs:normalizedString" use="required"><xs:annotation><xs:documentation>Name of SimpleType element. &amp;quot;name&amp;quot; must be unique with respect to all other elements of the TypeDefinitions list. Furthermore, &amp;quot;name&amp;quot; of a SimpleType must be different to all &amp;quot;name&amp;quot;s of ScalarVariable.</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="description" type="xs:string"><xs:annotation><xs:documentation>Description of the SimpleType</xs:documentation></xs:annotation></xs:attribute></xs:complexType><xs:annotation><xs:documentation>Copyright(c) 2008-2011, MODELISAR consortium. All rights reserved.This file is licensed by the copyright holders under the BSD License(http://www.opensource.org/licenses/bsd-license.html):----------------------------------------------------------------------------Redistribution and use in source and binary forms, with or withoutmodification, are permitted provided that the following conditions are met:- Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.- Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.- Neither the name of the copyright holders nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS&amp;quot;AS IS&amp;quot; AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITEDTO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULARPURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER ORCONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OROTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IFADVISED OF THE POSSIBILITY OF SUCH DAMAGE.----------------------------------------------------------------------------with the extension:You may distribute or publicly perform any modification only under theterms of this license.(Note, this means that if you distribute a modified file,the modified file must also be provided under this license).</xs:documentation></xs:annotation><xs:element name="fmiModelDescription"><xs:complexType><xs:sequence><xs:sequence maxOccurs="2"><xs:annotation><xs:documentation>At least one of the elements must be present</xs:documentation></xs:annotation><xs:element name="ModelExchange" minOccurs="0"><xs:annotation><xs:documentation>The FMU includes a model or the communication to a tool that provides a model. The environment provides the simulation engine for the model.</xs:documentation></xs:annotation><xs:complexType><xs:annotation><xs:documentation>List of capability flags that an FMI2 Model Exchange interface can provide</xs:documentation></xs:annotation><xs:sequence><xs:element name="SourceFiles" minOccurs="0"><xs:annotation><xs:documentation>List of source file names that are present in the &amp;quot;sources&amp;quot; directory of the FMU and need to be compiled in order to generate the binary of the FMU (only meaningful for source code FMUs).</xs:documentation></xs:annotation><xs:complexType><xs:sequence maxOccurs="unbounded"><xs:element name="File"><xs:complexType><xs:attribute name="name" type="xs:normalizedString" use="required"><xs:annotation><xs:documentation>Name of the file including the path relative to the sources directory, using the forward slash as separator (for example: name = &amp;quot;myFMU.c&amp;quot;; name = &amp;quot;modelExchange/solve.c&amp;quot;)</xs:documentation></xs:annotation></xs:attribute></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:sequence><xs:attribute name="modelIdentifier" type="xs:normalizedString" use="required"><xs:annotation><xs:documentation>Short class name according to C-syntax, e.g. &amp;quot;A_B_C&amp;quot;. Used as prefix for FMI2 functions if the functions are provided in C source code or in static libraries, but not if the functions are provided by a DLL/SharedObject. modelIdentifier is also used as name of the static library or DLL/SharedObject.</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="needsExecutionTool" type="xs:boolean" default="false"><xs:annotation><xs:documentation>If true, a tool is needed to execute the model and the FMU just contains the communication to this tool.</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="completedIntegratorStepNotNeeded" type="xs:boolean" default="false"></xs:attribute><xs:attribute name="canBeInstantiatedOnlyOncePerProcess" type="xs:boolean" default="false"></xs:attribute><xs:attribute name="canNotUseMemoryManagementFunctions" type="xs:boolean" default="false"></xs:attribute><xs:attribute name="canGetAndSetFMUstate" type="xs:boolean" default="false"></xs:attribute><xs:attribute name="canSerializeFMUstate" type="xs:boolean" default="false"></xs:attribute><xs:attribute name="providesDirectionalDerivative" type="xs:boolean" default="false"></xs:attribute></xs:complexType></xs:element><xs:element name="CoSimulation" minOccurs="0"><xs:annotation><xs:documentation>The FMU includes a model and the simulation engine, or the communication to a tool that provides this. The environment provides the master algorithm for the Co-Simulation coupling.</xs:documentation></xs:annotation><xs:complexType><xs:sequence><xs:element name="SourceFiles" minOccurs="0"><xs:annotation><xs:documentation>List of source file names that are present in the &amp;quot;sources&amp;quot; directory of the FMU and need to be compiled in order to generate the binary of the FMU (only meaningful for source code FMUs).</xs:documentation></xs:annotation><xs:complexType><xs:sequence maxOccurs="unbounded"><xs:element name="File"><xs:complexType><xs:attribute name="name" type="xs:normalizedString" use="required"><xs:annotation><xs:documentation>Name of the file including the path relative to the sources directory, using the forward slash as separator (for example: name = &amp;quot;myFMU.c&amp;quot;; name = &amp;quot;coSimulation/solve.c&amp;quot;)</xs:documentation></xs:annotation></xs:attribute></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:sequence><xs:attribute name="modelIdentifier" type="xs:normalizedString" use="required"><xs:annotation><xs:documentation>Short class name according to C-syntax, e.g. &amp;quot;A_B_C&amp;quot;. Used as prefix for FMI2 functions if the functions are provided in C source code or in static libraries, but not if the functions are provided by a DLL/SharedObject. modelIdentifier is also used as name of the static library or DLL/SharedObject.</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="needsExecutionTool" type="xs:boolean" default="false"><xs:annotation><xs:documentation>If true, a tool is needed to execute the model and the FMU just contains the communication to this tool.</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="canHandleVariableCommunicationStepSize" type="xs:boolean" default="false"></xs:attribute><xs:attribute name="canInterpolateInputs" type="xs:boolean" default="false"></xs:attribute><xs:attribute name="maxOutputDerivativeOrder" type="xs:unsignedInt" default="0"></xs:attribute><xs:attribute name="canRunAsynchronuously" type="xs:boolean" default="false"></xs:attribute><xs:attribute name="canBeInstantiatedOnlyOncePerProcess" type="xs:boolean" default="false"></xs:attribute><xs:attribute name="canNotUseMemoryManagementFunctions" type="xs:boolean" default="false"></xs:attribute><xs:attribute name="canGetAndSetFMUstate" type="xs:boolean" default="false"></xs:attribute><xs:attribute name="canSerializeFMUstate" type="xs:boolean" default="false"></xs:attribute><xs:attribute name="providesDirectionalDerivative" type="xs:boolean" default="false"><xs:annotation><xs:documentation>Directional derivatives at communication points</xs:documentation></xs:annotation></xs:attribute></xs:complexType></xs:element></xs:sequence><xs:element name="UnitDefinitions" minOccurs="0"><xs:complexType><xs:sequence maxOccurs="unbounded"><xs:element name="Unit" type="fmi2Unit"></xs:element></xs:sequence></xs:complexType></xs:element><xs:element name="TypeDefinitions" minOccurs="0"><xs:complexType><xs:sequence maxOccurs="unbounded"><xs:element name="SimpleType" type="fmi2SimpleType"></xs:element></xs:sequence></xs:complexType></xs:element><xs:element name="LogCategories" minOccurs="0"><xs:annotation><xs:documentation>Log categories available in FMU</xs:documentation></xs:annotation><xs:complexType><xs:sequence maxOccurs="unbounded"><xs:element name="Category"><xs:complexType><xs:attribute name="name" type="xs:normalizedString" use="required"><xs:annotation><xs:documentation>Name of Category element. &amp;quot;name&amp;quot; must be unique with respect to all other elements of the LogCategories list. Standardized names: &amp;quot;logEvents&amp;quot;, &amp;quot;logSingularLinearSystems&amp;quot;, &amp;quot;logNonlinearSystems&amp;quot;, &amp;quot;logDynamicStateSelection&amp;quot;, &amp;quot;logStatusWarning&amp;quot;, &amp;quot;logStatusDiscard&amp;quot;, &amp;quot;logStatusError&amp;quot;, &amp;quot;logStatusFatal&amp;quot;, &amp;quot;logStatusPending&amp;quot;, &amp;quot;logAll&amp;quot;</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="description" type="xs:string"><xs:annotation><xs:documentation>Description of the log category</xs:documentation></xs:annotation></xs:attribute></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element><xs:element name="DefaultExperiment" minOccurs="0"><xs:complexType><xs:attribute name="startTime" type="xs:double"><xs:annotation><xs:documentation>Default start time of simulation</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="stopTime" type="xs:double"><xs:annotation><xs:documentation>Default stop time of simulation</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="tolerance" type="xs:double"><xs:annotation><xs:documentation>Default relative integration tolerance</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="stepSize" type="xs:double"><xs:annotation><xs:documentation>ModelExchange: Default step size for fixed step integrators.CoSimulation: Preferred communicationStepSize.</xs:documentation></xs:annotation></xs:attribute></xs:complexType></xs:element><xs:element name="VendorAnnotations" type="fmi2Annotation" minOccurs="0"><xs:annotation><xs:documentation>Tool specific data (ignored by other tools)</xs:documentation></xs:annotation></xs:element><xs:element name="ModelVariables"><xs:annotation><xs:documentation>Ordered list of all variables (first definition has index = 1).</xs:documentation></xs:annotation><xs:complexType><xs:sequence maxOccurs="unbounded"><xs:element name="ScalarVariable" type="fmi2ScalarVariable"></xs:element></xs:sequence></xs:complexType></xs:element><xs:element name="ModelStructure"><xs:annotation><xs:documentation>Ordered lists of outputs, exposed state derivatives,and the initial unknowns. Optionally, the functionaldependency of these variables can be defined.</xs:documentation></xs:annotation><xs:complexType><xs:sequence><xs:element name="Outputs" type="fmi2VariableDependency" minOccurs="0"><xs:annotation><xs:documentation>Ordered list of all outputs. Exactly all variables with causality=&amp;quot;output&amp;quot; must be in this list. The dependency definition holds for Continuous-Time and for Event Mode (ModelExchange) and for Communication Points (CoSimulation).</xs:documentation></xs:annotation></xs:element><xs:element name="Derivatives" type="fmi2VariableDependency" minOccurs="0"><xs:annotation><xs:documentation>Ordered list of all exposed state derivatives (and therefore implicitely associated continuous-time states). Exactly all state derivatives of a ModelExchange FMU must be in this list. A CoSimulation FMU need not expose its state derivatives. If a model has dynamic state selection, introduce dummy state variables. The dependency definition holds for Continuous-Time and for Event Mode (ModelExchange) and for Communication Points (CoSimulation).</xs:documentation></xs:annotation></xs:element><xs:element name="InitialUnknowns" minOccurs="0"><xs:annotation><xs:documentation>Ordered list of all exposed Unknowns in Initialization Mode. This list consists of all variables with (1) causality = &amp;quot;output&amp;quot; and (initial=&amp;quot;approx&amp;quot; or calculated&amp;quot;), (2) causality = &amp;quot;calculatedParameter&amp;quot;, and (3) all continuous-time states and all state derivatives (defined with element Derivatives from ModelStructure)with initial=(&amp;quot;approx&amp;quot; or &amp;quot;calculated&amp;quot;). The resulting list is not allowed to have duplicates (e.g. if a state is also an output, it is included only once in the list). The Unknowns in this list must be ordered according to their ScalarVariable index (e.g. if for two variables A and B the ScalarVariable index of A is less than the index of B, then A must appear before B in InitialUnknowns).</xs:documentation></xs:annotation><xs:complexType><xs:sequence maxOccurs="unbounded"><xs:element name="Unknown"><xs:annotation><xs:documentation>Dependency of scalar Unknown from Knowns: Unknown=f(Known_1, Known_2, ...).The Knowns are &amp;quot;inputs&amp;quot;,&amp;quot;variables with initial=exact&amp;quot;, and&amp;quot;independent variable&amp;quot;.</xs:documentation></xs:annotation><xs:complexType><xs:attribute name="index" type="xs:unsignedInt" use="required"><xs:annotation><xs:documentation>ScalarVariable index of Unknown</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="dependencies"><xs:annotation><xs:documentation>Defines the dependency of the Unknown (directly or indirectly via auxiliary variables) on the Knowns in the Initialization Mode. If not present, it must be assumed that the Unknown depends on all Knowns. If present as empty list, the Unknown depends on none of the Knowns. Otherwise the Unknown depends on the Knowns defined by the given ScalarVariable indices. The indices are ordered according to size, starting with the smallest index.</xs:documentation></xs:annotation><xs:simpleType><xs:list itemType="xs:unsignedInt"></xs:list></xs:simpleType></xs:attribute><xs:attribute name="dependenciesKind"><xs:annotation><xs:documentation>If not present, it must be assumed that the Unknown depends on the Knowns without a particular structure. Otherwise, the corresponding Known v enters the equation as:= &amp;quot;dependent&amp;quot;: no particular structure, f(v)= &amp;quot;constant&amp;quot; : constant factor, c*v (only for Real variables)If &amp;quot;dependenciesKind&amp;quot; is present, &amp;quot;dependencies&amp;quot; must be present and must have the same number of list elements.</xs:documentation></xs:annotation><xs:simpleType><xs:list><xs:simpleType><xs:restriction base="xs:normalizedString"><xs:enumeration value="dependent"></xs:enumeration><xs:enumeration value="constant"></xs:enumeration><xs:enumeration value="fixed"></xs:enumeration><xs:enumeration value="tunable"></xs:enumeration><xs:enumeration value="discrete"></xs:enumeration></xs:restriction></xs:simpleType></xs:list></xs:simpleType></xs:attribute></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:sequence><xs:attribute name="fmiVersion" type="xs:normalizedString" use="required" fixed="2.0"><xs:annotation><xs:documentation>Version of FMI (FMI 2.0 revision is defined as &amp;quot;2.0&amp;quot;; future minor revisions are denoted as 2.0.1, 2.0.2 etc).</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="modelName" type="xs:string" use="required"><xs:annotation><xs:documentation>Class name of FMU, e.g. &amp;quot;A.B.C&amp;quot; (several FMU instances are possible)</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="guid" type="xs:normalizedString" use="required"><xs:annotation><xs:documentation>Fingerprint of xml-file content to verify that xml-file and C-functions are compatible to each other</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="description" type="xs:string"></xs:attribute><xs:attribute name="author" type="xs:string"></xs:attribute><xs:attribute name="version" type="xs:normalizedString"><xs:annotation><xs:documentation>Version of FMU, e.g., &amp;quot;1.4.1&amp;quot;</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="copyright" type="xs:string"><xs:annotation><xs:documentation>Information on intellectual property copyright for this FMU, such as &amp;quot;(c) MyCompany 2011&amp;quot;</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="license" type="xs:string"><xs:annotation><xs:documentation>Information on intellectual property licensing for this FMU, such as &amp;quot;BSD license&amp;quot;, &amp;quot;Proprietary&amp;quot;, or &amp;quot;Public Domain&amp;quot;</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="generationTool" type="xs:normalizedString"></xs:attribute><xs:attribute name="generationDateAndTime" type="xs:dateTime"></xs:attribute><xs:attribute name="variableNamingConvention" use="optional" default="flat"><xs:simpleType><xs:restriction base="xs:normalizedString"><xs:enumeration value="flat"></xs:enumeration><xs:enumeration value="structured"></xs:enumeration></xs:restriction></xs:simpleType></xs:attribute><xs:attribute name="numberOfEventIndicators" type="xs:unsignedInt"></xs:attribute></xs:complexType></xs:element><xs:attributeGroup name="fmi2RealAttributes"><xs:attribute name="quantity" type="xs:normalizedString"></xs:attribute><xs:attribute name="unit" type="xs:normalizedString"></xs:attribute><xs:attribute name="displayUnit" type="xs:normalizedString"><xs:annotation><xs:documentation>Default display unit, provided the conversion of values in &amp;quot;unit&amp;quot; to values in &amp;quot;displayUnit&amp;quot; is defined in UnitDefinitions / Unit / DisplayUnit.</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="relativeQuantity" type="xs:boolean" default="false"><xs:annotation><xs:documentation>If relativeQuantity=true, offset for displayUnit must be ignored.</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="min" type="xs:double"></xs:attribute><xs:attribute name="max" type="xs:double"><xs:annotation><xs:documentation>max &amp;gt;= min required</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="nominal" type="xs:double"><xs:annotation><xs:documentation>nominal &amp;gt; 0.0 required</xs:documentation></xs:annotation></xs:attribute><xs:attribute name="unbounded" type="xs:boolean" default="false"><xs:annotation><xs:documentation>Set to true, e.g., for crank angle. If true and variable is a state, relative tolerance should be zero on this variable.</xs:documentation></xs:annotation></xs:attribute></xs:attributeGroup><xs:attributeGroup name="fmi2IntegerAttributes"><xs:attribute name="quantity" type="xs:normalizedString"></xs:attribute><xs:attribute name="min" type="xs:int"></xs:attribute><xs:attribute name="max" type="xs:int"><xs:annotation><xs:documentation>max &amp;gt;= min required</xs:documentation></xs:annotation></xs:attribute></xs:attributeGroup><xs:complexType name="fmi2Annotation"><xs:sequence maxOccurs="unbounded"><xs:element name="Tool"><xs:annotation><xs:documentation>Tool specific annotation (ignored by other tools).</xs:documentation></xs:annotation><xs:complexType><xs:sequence><xs:any namespace="##any" processContents="lax" minOccurs="0"></xs:any></xs:sequence><xs:attribute name="name" type="xs:normalizedString" use="required"><xs:annotation><xs:documentation>Name of tool that can interpret the annotation. &amp;quot;name&amp;quot; must be unique with respect to all other elements of the VendorAnnotation list.</xs:documentation></xs:annotation></xs:attribute></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:schema>'

fmi2Component            = c_void_p
fmi2ComponentEnvironment = c_void_p
fmi2FMUstate             = c_void_p
fmi2ValueReference       = c_uint
fmi2Real                 = c_double
fmi2Integer              = c_int
fmi2Boolean              = c_int
fmi2Char                 = c_char
fmi2String               = c_char_p
fmi2Type                 = c_int
fmi2Byte                 = c_char

fmi2Status = c_int

fmi2CallbackLoggerTYPE         = CFUNCTYPE(None, fmi2ComponentEnvironment, fmi2String, fmi2Status, fmi2String, fmi2String)
fmi2CallbackAllocateMemoryTYPE = CFUNCTYPE(c_void_p, c_size_t, c_size_t)
fmi2CallbackFreeMemoryTYPE     = CFUNCTYPE(None, c_void_p)
fmi2StepFinishedTYPE           = CFUNCTYPE(None, fmi2ComponentEnvironment, fmi2Status)

fmi2ModelExchange = 0
fmi2CoSimulation  = 1

fmi2True  = 1
fmi2False = 0

fmi2StatusKind = c_int
fmi2DoStepStatus       = 0
fmi2PendingStatus      = 1
fmi2LastSuccessfulTime = 2
fmi2Terminated         = 3

calloc          = cdll.msvcrt.calloc
calloc.argtypes = [c_size_t, c_size_t]
calloc.restype  = c_void_p

free = cdll.msvcrt.free
free.argtypes = [c_void_p]

def logger(a, b, c, d, e):
    print a, b, c, d, e

def allocateMemory(nobj, size):
    return calloc(nobj, size)

def freeMemory(obj):
    free(obj)

def stepFinished(componentEnvironment, status):
    print combinations, status

class fmi2CallbackFunctions(Structure):
    _fields_ = [('logger',               fmi2CallbackLoggerTYPE),
                ('allocateMemory',       fmi2CallbackAllocateMemoryTYPE),
                ('freeMemory',           fmi2CallbackFreeMemoryTYPE),
                ('stepFinished',         fmi2StepFinishedTYPE),
                ('componentEnvironment', fmi2ComponentEnvironment)]

callbacks = fmi2CallbackFunctions()
callbacks.logger               = fmi2CallbackLoggerTYPE(logger)
callbacks.allocateMemory       = fmi2CallbackAllocateMemoryTYPE(allocateMemory)
callbacks.stepFinished         = fmi2StepFinishedTYPE(stepFinished)
callbacks.freeMemory           = fmi2CallbackFreeMemoryTYPE(freeMemory)
callbacks.componentEnvironment = None

variables = {}

class ScalarVariable(object):

    def __init__(self, name, valueReference):
        self.name = name
        self.valueReference = valueReference
        self.description = None
        self.type = None
        self.start = None
        self.causality = None
        self.variability = None

class FMU2(object):

    def __init__(self, unzipdir):

        self.unzipdir = unzipdir

        schema_tree = etree.fromstring(FMI2_SCHEMA)
        schema = etree.XMLSchema(etree=schema_tree)
        parser = etree.XMLParser(schema = schema)

        tree = etree.parse(os.path.join(unzipdir, 'modelDescription.xml'), parser=parser)

        root = tree.getroot()

        self.guid       = root.get('guid')
        self.fmiVersion = root.get('fmiVersion')
        self.modelName  = root.get('modelName')
        self.causality  = root.get('causality')
        self.variability  = root.get('variability')

        coSimulation = root.find('CoSimulation')
        self.modelIdentifier = coSimulation.get('modelIdentifier')

        modelVariables = root.find('ModelVariables')

        self.variables = {}
        self.variableNames = []

        for variable in modelVariables:
            sv = ScalarVariable(name=variable.get('name'), valueReference=int(variable.get('valueReference')))
            sv.description = variable.get('description')
            sv.start = variable.get('start')

            value = next(variable.iterchildren())
            sv.type = value.tag
            start = value.get('start')

            if start is not None:
                if sv.type == 'Real':
                    sv.start = float(start)
                elif sv.type == 'Integer':
                    sv.start = int(start)
                elif sv.type == 'Boolean':
                    sv.start = start == 'true'
                else:
                    sv.start = start

            self.variableNames.append(sv.name)
            self.variables[sv.name] = sv

        library = cdll.LoadLibrary(os.path.join(unzipdir, 'binaries', 'win32', self.modelIdentifier + '.dll'))
        self.dll = library

        self.fmi2Instantiate = getattr(library, 'fmi2Instantiate')
        self.fmi2Instantiate.argtypes = [fmi2String, fmi2Type, fmi2String, fmi2String, POINTER(fmi2CallbackFunctions), fmi2Boolean, fmi2Boolean]
        self.fmi2Instantiate.restype = fmi2ComponentEnvironment

        self.fmi2SetupExperiment          = getattr(library, 'fmi2SetupExperiment')
        self.fmi2SetupExperiment.argtypes = [fmi2Component, fmi2Boolean, fmi2Real, fmi2Real, fmi2Boolean, fmi2Real]
        self.fmi2SetupExperiment.restype  = fmi2Status

        self.fmi2EnterInitializationMode          = getattr(library, 'fmi2EnterInitializationMode')
        self.fmi2EnterInitializationMode.argtypes = [fmi2Component]
        self.fmi2EnterInitializationMode.restype  = fmi2Status

        self.fmi2ExitInitializationMode          = getattr(library, 'fmi2ExitInitializationMode')
        self.fmi2ExitInitializationMode.argtypes = [fmi2Component]
        self.fmi2ExitInitializationMode.restype  = fmi2Status

        self.fmi2DoStep          = getattr(library, 'fmi2DoStep')
        self.fmi2DoStep.argtypes = [fmi2Component, fmi2Real, fmi2Real, fmi2Boolean]
        self.fmi2DoStep.restype  = fmi2Status

        self.fmi2GetReal          = getattr(library, 'fmi2GetReal')
        self.fmi2GetReal.argtypes = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Real)]
        self.fmi2GetReal.restype  = fmi2Status

        self.fmi2GetInteger          = getattr(library, 'fmi2GetInteger')
        self.fmi2GetInteger.argtypes = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Integer)]
        self.fmi2GetInteger.restype  = fmi2Status

        self.fmi2GetBoolean          = getattr(library, 'fmi2GetBoolean')
        self.fmi2GetBoolean.argtypes = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Boolean)]
        self.fmi2GetBoolean.restype  = fmi2Status

        self.fmi2SetReal          = getattr(library, 'fmi2SetReal')
        self.fmi2SetReal.argtypes = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Real)]
        self.fmi2SetReal.restype  = fmi2Status

        self.fmi2SetInteger          = getattr(library, 'fmi2SetInteger')
        self.fmi2SetInteger.argtypes = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Integer)]
        self.fmi2SetInteger.restype  = fmi2Status

        self.fmi2SetBoolean          = getattr(library, 'fmi2SetBoolean')
        self.fmi2SetBoolean.argtypes = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Boolean)]
        self.fmi2SetBoolean.restype  = fmi2Status

        self.fmi2GetBooleanStatus          = getattr(library, 'fmi2GetBooleanStatus')
        self.fmi2GetBooleanStatus.argtypes = [fmi2Component, fmi2StatusKind, POINTER(fmi2Boolean)]
        self.fmi2GetBooleanStatus.restype  = fmi2Status

        self.fmi2Terminate          = getattr(library, 'fmi2Terminate')
        self.fmi2Terminate.argtypes = [fmi2Component]
        self.fmi2Terminate.restype  = fmi2Status

        self.fmi2FreeInstance          = getattr(library, 'fmi2FreeInstance')
        self.fmi2FreeInstance.argtypes = [fmi2Component]
        self.fmi2FreeInstance.restype  = None

    def instantiate(self, instance_name, kind):
        self.component = self.fmi2Instantiate(instance_name, kind, self.guid, 'file://' + self.unzipdir, byref(callbacks), fmi2False, fmi2False)

    def setupExperiment(self, tolerance, startTime, stopTime=None):

        toleranceDefined = tolerance is not None

        if tolerance is None:
            tolerance = 0.0

        stopTimeDefined = stopTime is not None

        if stopTime is None:
            stopTime = 0.0

        status = self.fmi2SetupExperiment(self.component, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime)

    def enterInitializationMode(self):
        status = self.fmi2EnterInitializationMode(self.component)

    def exitInitializationMode(self):
        status = self.fmi2ExitInitializationMode(self.component)

    def doStep(self, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint):
        status = self.fmi2DoStep(self.component, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint)
        return status

    def getBooleanStatus(self, kind):
        value = fmi2Boolean(fmi2False)
        status = self.fmi2GetBooleanStatus(self.component, kind, byref(value))
        return value

    def getReal(self, vr):
        value = (fmi2Real * len(vr))()
        status = self.fmi2GetReal(self.component, vr, len(vr), value)
        return list(value)

    def setReal(self, vr, value):
        status = self.fmi2SetReal(self.component, vr, len(vr), value)

    def terminate(self):
        status = self.fmi2Terminate(self.component)

    def freeInstance(self):
        self.fmi2FreeInstance(self.component)
        windll.kernel32.FreeLibrary(self.dll._handle)
