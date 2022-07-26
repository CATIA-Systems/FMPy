within FMI;
class ExternalFMU
  extends ExternalObject;

  impure function constructor
      input FMI.ModelicaFunctions callbacks;
      input String unzipdir;
      input String modelIdentifier;
      input String instanceName;
      input Integer interfaceType;
      input String instantiationToken;
      input Boolean visible;
      input Boolean loggingOn;
      input Boolean logFMICalls;
      output ExternalFMU externalFMU;
  external"C" externalFMU =
        FMU_load(callbacks, unzipdir, modelIdentifier, instanceName, interfaceType, instantiationToken, visible, loggingOn, logFMICalls) annotation (Library="ModelicaFMI");

  end constructor;

  impure function destructor
    input ExternalFMU externalFMU;
  external"C" FMU_free(externalFMU) annotation (Library="ModelicaFMI");
  end destructor;

  annotation (Icon(coordinateSystem(preserveAspectRatio=false), graphics={
          Rectangle(
            lineColor={160,160,164},
            fillColor={160,160,164},
            fillPattern=FillPattern.Solid,
            extent={{-100,-100},{100,100}},
            radius=25.0)}),                                      Diagram(
        coordinateSystem(preserveAspectRatio=false)));
end ExternalFMU;
