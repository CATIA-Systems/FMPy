within FMI.FMI2.Functions;
impure function FMI2GetContinuousStates
  input Internal.ExternalFMU instance;
    output Real x[nx];
    input Integer nx;
    external"C" FMU_FMI2GetContinuousStates(instance, x, nx) annotation (Library="ModelicaFMI");
end FMI2GetContinuousStates;
