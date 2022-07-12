model @=modelIdentifier=@

  import FMI.FMI2.*;

  parameter String instanceName = "@=instanceName=@";

  parameter Real startTime = 0.0;

  parameter Real stopTime = Modelica.Constants.inf;

  parameter Real tolerance = 0.0;

  parameter Boolean visible = false;

  parameter Boolean loggingOn = false;

  parameter Real communicationStepSize = @=communicationStepSize=@;
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

protected

  FMI.ExternalFMU instance = FMI.ExternalFMU(FMI.ModelicaFunctions(),
    Modelica.Utilities.Files.loadResource("modelica://FMITest/Resources/FMUs/@=modelIdentifier=@"),
    "@=modelIdentifier=@",
    1,
    "@=instantiationToken=@",
    visible,
    loggingOn);

initial algorithm

@@ for variable in parameters @@
  FMI2SetReal(instance, {@=variable.valueReference=@}, 1, {@=variable.name=@});
@@ endfor @@

  FMI2SetupExperiment(instance, tolerance > 0.0, tolerance, startTime, stopTime < Modelica.Constants.inf, stopTime);
  FMI2EnterInitializationMode(instance);

@@ for variable in real_inputs @@
  FMI2SetReal(instance, {@=variable.valueReference=@}, 1, {@=variable.name=@_start});
@@ endfor @@

  FMI2ExitInitializationMode(instance);

algorithm

  when sample(startTime, communicationStepSize) then

@@ for variable in inputs @@
    FMI2Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {@=variable.name=@});
@@ endfor @@

    FMI2DoStep(instance, time, communicationStepSize, true);

@@ for variable in outputs @@
    @=variable.name=@ = FMI2Get@=variable.type=@Scalar(instance, @=variable.valueReference=@);
@@ endfor @@

  end when;

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
