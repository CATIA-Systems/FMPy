within FMI.FMI3.Functions;
impure function FMI3GetContinuousStates
  input Internal.ExternalFMU instance;
    output Real continuousStates[nContinuousStates];
    input Integer nContinuousStates;
    external"C" FMU_FMI3GetContinuousStates(instance, continuousStates, nContinuousStates) annotation (Library="ModelicaFMI");
end FMI3GetContinuousStates;
