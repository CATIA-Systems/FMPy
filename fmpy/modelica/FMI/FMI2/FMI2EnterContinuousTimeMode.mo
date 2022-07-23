within FMI.FMI2;
function FMI2EnterContinuousTimeMode
    input ExternalFMU externalFMU;
    external"C" FMU_FMI2EnterContinuousTimeMode(externalFMU) annotation (Library="ModelicaFMI");
end FMI2EnterContinuousTimeMode;
