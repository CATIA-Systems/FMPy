within FMI.FMI2;
function FMI2SetBoolean
    input ExternalFMU externalFMU;
    input Integer vr[nvr];
    input Integer nvr;
    input Boolean value[nvr];
    external"C" FMU_FMI2SetBoolean(externalFMU, vr, nvr, value) annotation (Library="ModelicaFMI");
end FMI2SetBoolean;
