within FMI.FMI2;
function FMI2SetInteger
    input ExternalFMU externalFMU;
    input Integer vr[nvr];
    input Integer nvr;
    input Integer value[nvr];
    external"C" FMU_FMI2SetInteger(externalFMU, vr, nvr, value) annotation (Library="ModelicaFMI");
end FMI2SetInteger;
