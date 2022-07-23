within FMI.FMI2;
function FMI2NewDiscreteStates
    input ExternalFMU externalFMU;
    output Boolean valuesOfContinuousStatesChanged;
    output Real nextEventTime;
    external"C" FMU_FMI2NewDiscreteStates(externalFMU, valuesOfContinuousStatesChanged, nextEventTime) annotation (Library="ModelicaFMI");
end FMI2NewDiscreteStates;
