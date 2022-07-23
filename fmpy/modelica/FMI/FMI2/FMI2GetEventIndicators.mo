within FMI.FMI2;
function FMI2GetEventIndicators
  input ExternalFMU instance;
  input Integer ni;
  output Real eventIndicators[ni];
  external"C" FMU_FMI2GetEventIndicators(instance, eventIndicators, ni) annotation (Library="ModelicaFMI");
end FMI2GetEventIndicators;
