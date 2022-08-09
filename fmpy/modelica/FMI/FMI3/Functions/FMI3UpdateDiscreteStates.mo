within FMI.FMI3.Functions;
impure function FMI3UpdateDiscreteStates
  input Internal.ExternalFMU externalFMU;
    output Boolean valuesOfContinuousStatesChanged;
    output Real nextEventTime;
    external"C" FMU_FMI3UpdateDiscreteStates(externalFMU, valuesOfContinuousStatesChanged, nextEventTime) annotation (Library="ModelicaFMI");
end FMI3UpdateDiscreteStates;
