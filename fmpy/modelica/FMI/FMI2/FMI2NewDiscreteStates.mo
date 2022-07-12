within FMI.FMI2;
function FMI2NewDiscreteStates
    input ExternalFMU externalFMU;
    external"C" FMU_FMI2NewDiscreteStates(externalFMU) annotation (Library="ModelicaFMI");
end FMI2NewDiscreteStates;
