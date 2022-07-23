within FMI.FMI2;
function FMI2EnterEventMode
    input ExternalFMU externalFMU;
    external"C" FMU_FMI2EnterEventMode(externalFMU) annotation (Library="ModelicaFMI");
end FMI2EnterEventMode;
