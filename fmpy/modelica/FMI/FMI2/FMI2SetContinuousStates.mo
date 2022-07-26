within FMI.FMI2;
impure function FMI2SetContinuousStates
  input Internal.ExternalFMU instance;
    input Real x[nx];
    input Integer nx;
    external"C" FMU_FMI2SetContinuousStates(instance, x, nx) annotation (Library="ModelicaFMI");
end FMI2SetContinuousStates;
