model @=modelName=@
@@ if description @@
  "@=description=@"
@@ endif @@

  import FMI.FMI2.*;

  parameter Modelica.Units.SI.Time startTime = 0.0 annotation(Dialog(tab="FMI", group="Parameters"));

  parameter Modelica.Units.SI.Time stopTime = Modelica.Constants.inf annotation(Dialog(tab="FMI", group="Parameters")));

  parameter Real tolerance = 0.0 annotation(Dialog(tab="FMI", group="Parameters")));

  parameter Boolean visible = false annotation(Dialog(tab="FMI", group="Parameters")));

  parameter Boolean loggingOn = false annotation(Dialog(tab="FMI", group="Parameters")));

  parameter Boolean logFMICalls = false annotation(Dialog(tab="FMI", group="Parameters")));
@@ block parameters @@
@@ endblock @@
@@ for variable in parameters @@

  parameter @=modelica_type(variable)=@ '@=variable.name=@' = @=start_value(variable)=@@@ if variable.description @@ "@=variable.description=@"@@ endif @@;
@@ endfor @@
@@ for variable in inputs @@

  parameter @=variable.type=@ '@=variable.name=@_start' = @=start_value(variable)=@;
@@ endfor @@
@@ for variable in inputs @@

  Modelica.Blocks.Interfaces.@=variable.type=@Input '@=variable.name=@'(start='@=variable.name=@_start') @=annotations[variable.name]=@;
@@ endfor @@
@@ for variable in outputs @@

  Modelica.Blocks.Interfaces.@=variable.type=@Output '@=variable.name=@' @=annotations[variable.name]=@;
@@ endfor @@

protected

  FMI.ExternalFMU instance = FMI.ExternalFMU(FMI.ModelicaFunctions(),
    Modelica.Utilities.Files.loadResource("modelica://@=package=@/Resources/FMUs/@=modelIdentifier=@"),
    "@=modelIdentifier=@",
    getInstanceName(),
    @=interfaceType=@,
    "@=instantiationToken=@",
    visible,
    loggingOn,
    logFMICalls);

@@ block equations @@
@@ endblock @@

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
end @=modelName=@;
