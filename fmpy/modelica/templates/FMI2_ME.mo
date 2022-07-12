model @=modelIdentifier=@

  import FMI.FMI2.*;

  parameter String instanceName = "@=instanceName=@";

  parameter Real startTime = 0.0;

  parameter Real stopTime = Modelica.Constants.inf;

  parameter Real tolerance = 0.0;

  parameter Boolean visible = false;

  parameter Boolean loggingOn = false;
@@ for variable in parameters @@

  parameter @=variable.type=@ @=variable.name=@ = @=variable.start=@ "@=variable.description=@";
@@ endfor @@
@@ for variable in inputs @@

  parameter @=variable.type=@ @=variable.name=@_start = @=variable.start=@;
@@ endfor @@
@@ for variable in inputs @@

  Modelica.Blocks.Interfaces.@=variable.type=@Input @=variable.name=@(start=@=variable.name=@_start) @=annotations[variable.name]=@;
@@ endfor @@
@@ for variable in outputs @@

  Modelica.Blocks.Interfaces.@=variable.type=@Output @=variable.name=@ @=annotations[variable.name]=@;
@@ endfor @@

//protected

  FMI.ExternalFMU instance = FMI.ExternalFMU(FMI.ModelicaFunctions(),
    Modelica.Utilities.Files.loadResource("modelica://FMITest/Resources/FMUs/@=modelIdentifier=@"),
    "@=modelIdentifier=@",
    0,
    "@=instantiationToken=@",
    visible,
    loggingOn);

  final constant Integer nx = @=nx=@;
  final constant Integer nz = @=nz=@;

  final constant Integer realInputVRs[@=realInputVRs|length=@] = @=as_array(realInputVRs, '0')=@;
  final constant Integer integerInputVRs[@=integerInputVRs|length=@] = @=as_array(integerInputVRs, '0')=@;
  final constant Integer booleanInputVRs[@=booleanInputVRs|length=@] = @=as_array(booleanInputVRs, '0')=@;

  parameter Real dummyStartTime(fixed=false);

  Real x[nx];
  Real z[nz];
  Real dummyTime;
  Boolean z_positive[nz];
  Boolean inputEvent;

  function setTimeAndStates
    input FMI.ExternalFMU instance;
    input Real t;
    input Real x[:];
    output Real dummyTime;
  algorithm
    FMI2SetTime(instance, t);
    FMI2SetContinuousStates(instance, x, size(x, 1));
    dummyTime := t;
  end setTimeAndStates;

  function getDerivatives
    input FMI.ExternalFMU instance;
    input Real dummyTime;
    output Real dx[nx];
  algorithm
    dx := FMI2GetDerivatives(instance, size(dx, 1));
  end getDerivatives;

  function getEventIndicators
    input FMI.ExternalFMU instance;
    input Real dummyTime;
    input Real realInputs[:];
    input Integer integerInputs[:];
    input Boolean booleanInputs[:];
    output Real z[nz];
  algorithm
    FMI2SetReal(instance, realInputVRs, size(realInputs, 1), realInputs);
    FMI2SetInteger(instance, integerInputVRs, size(integerInputs, 1), integerInputs);
    FMI2SetBoolean(instance, booleanInputVRs, size(booleanInputs, 1), booleanInputs);
    z := FMI2GetEventIndicators(instance, size(z, 1));
  end getEventIndicators;

  function updateDiscreteStates
    input FMI.ExternalFMU instance;
    output Real x[nx];
  algorithm
    FMI2EnterEventMode(instance);
    FMI2NewDiscreteStates(instance);
    FMI2EnterContinuousTimeMode(instance);
    x := FMI2GetContinuousStates(instance, size(x, 1));
  end updateDiscreteStates;

  function setInputs
    input FMI.ExternalFMU instance;
    input Integer[:] integerInputs;
    input Boolean[:] booleanInputs;
    output Boolean inputEvent;
  algorithm
    FMI2SetInteger(instance, integerInputVRs, size(integerInputs, 1), integerInputs);
    FMI2SetBoolean(instance, booleanInputVRs, size(booleanInputs, 1), booleanInputs);
    inputEvent :=true;
  end setInputs;

initial algorithm

  FMI2SetupExperiment(instance, tolerance > 0.0, tolerance, startTime, stopTime < Modelica.Constants.inf, stopTime);
  FMI2EnterInitializationMode(instance);
  FMI2ExitInitializationMode(instance);
  FMI2NewDiscreteStates(instance);
  FMI2EnterContinuousTimeMode(instance);
  x := FMI2GetContinuousStates(instance, nx);
  dummyStartTime :=time;

equation

  dummyTime = setTimeAndStates(instance, time, x);

  der(x) = getDerivatives(instance, dummyTime);

  z = getEventIndicators(instance, dummyTime, @=as_array(realInputs, '0.0')=@, @=as_array(integerInputs, '0')=@, @=as_array(booleanInputs, 'false')=@);

  for i in 1:size(z, 1) loop
    z_positive[i] = z[i] > 0;
  end for;

  inputEvent = setInputs(instance, @=as_array(integerInputs, '0')=@, @=as_array(booleanInputs, 'false')=@);

  when cat(1, change(z_positive), {inputEvent}) then
@@ if nx > 0 @@
    reinit(x, updateDiscreteStates(instance));
@@ else @@
    updateDiscreteStates(instance);
@@ endif @@
  end when;

  if initial() then
@@ for variable in outputs @@
@@ if variable.type == 'Real' @@
    @=variable.name=@ = FMI2GetRealScalar(instance, @=variable.valueReference=@, dummyStartTime);
@@ endif @@
@@ endfor @@
  else
@@ for variable in outputs @@
@@ if variable.type == 'Real' @@
    @=variable.name=@ = FMI2GetRealScalar(instance, @=variable.valueReference=@, dummyTime);
@@ endif @@
@@ endfor @@
  end if;

algorithm
  if initial() then
    FMI2SetTime(instance, dummyStartTime);
@@ for variable in inputs @@
@@ if variable.type != 'Real' @@
    // FMI2Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {@=variable.name=@});
@@ endif @@
@@ endfor @@
@@ for variable in outputs @@
@@ if variable.type != 'Real' @@
    @=variable.name=@ := FMI2Get@=variable.type=@Scalar(instance, @=variable.valueReference=@);
@@ endif @@
@@ endfor @@
  else
    FMI2SetTime(instance, dummyTime);
@@ for variable in inputs @@
@@ if variable.type != 'Real' @@
    // FMI2Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {@=variable.name=@});
@@ endif @@
@@ endfor @@
@@ for variable in outputs @@
@@ if variable.type != 'Real' @@
    @=variable.name=@ := FMI2Get@=variable.type=@Scalar(instance, @=variable.valueReference=@);
@@ endif @@
@@ endfor @@  end if;

  annotation (
    Icon(coordinateSystem(
      preserveAspectRatio=false,
      extent={{@=x0=@,@=y0=@}, {@=x1=@,@=y1=@}}),
      graphics={
        Text(extent={{@=x0=@,@=y1+10=@}, {@=x1=@,@=y1+50=@}}, lineColor={0,0,255}, textString="%name"),
        Rectangle(extent={{@=x0=@,@=y0=@},{@=x1=@,@=y1=@}}, lineColor={95,95,95}, fillColor={255,255,255}, fillPattern=FillPattern.Solid)
        @=labels=@
      }
    ),
    Diagram(coordinateSystem(preserveAspectRatio=false, extent={{@=x0=@,@=y0=@}, {@=x1=@,@=y1=@}}))
  );
end @=modelIdentifier=@;
