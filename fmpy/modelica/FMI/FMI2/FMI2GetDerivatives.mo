within FMI.FMI2;
function FMI2GetDerivatives
  input ExternalFMU instance;
  input Integer nx;
  output Real derivatives[nx];
  external"C" FMU_FMI2GetDerivatives(instance, derivatives, nx) annotation (Library="ModelicaFMI");
end FMI2GetDerivatives;
