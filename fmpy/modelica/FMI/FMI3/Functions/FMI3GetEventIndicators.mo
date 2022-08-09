within FMI.FMI3.Functions;
impure function FMI3GetEventIndicators
  input Internal.ExternalFMU instance;
  input Integer nEventIndicators;
  output Real eventIndicators[nEventIndicators];
  external"C" FMU_FMI3GetEventIndicators(instance, eventIndicators, nEventIndicators) annotation (Library="ModelicaFMI");
end FMI3GetEventIndicators;
