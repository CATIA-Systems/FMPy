within FMI.FMI2;
function FMI2ExitInitializationMode
    input ExternalFMU externalFMU;
    external"C" FMU_FMI2ExitInitializationMode(externalFMU) annotation (Library="ModelicaFMI");
end FMI2ExitInitializationMode;
