within FMI.FMI2;
function FMI2SetTime
    input ExternalFMU externalFMU;
    input Real t;
    external"C" FMU_FMI2SetTime(externalFMU, t) annotation (Library="ModelicaFMI");
end FMI2SetTime;
