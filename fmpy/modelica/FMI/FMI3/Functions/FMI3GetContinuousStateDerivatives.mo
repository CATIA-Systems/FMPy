within FMI.FMI3.Functions;
impure function FMI3GetContinuousStateDerivatives
  input Internal.ExternalFMU instance;
  input Integer nContinuousStates;
  output Real derivatives[nContinuousStates];
  external"C" FMU_FMI3GetContinuousStateDerivatives(instance, derivatives, nContinuousStates) annotation (Library="ModelicaFMI");
end FMI3GetContinuousStateDerivatives;
