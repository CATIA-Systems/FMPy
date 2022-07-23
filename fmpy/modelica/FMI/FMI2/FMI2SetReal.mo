within FMI.FMI2;
function FMI2SetReal
    input ExternalFMU externalFMU;
    input Integer vr[nvr];
    input Integer nvr;
    input Real value[nvr];
    external"C" FMU_FMI2SetReal(externalFMU, vr, nvr, value) annotation (Library="ModelicaFMI");
end FMI2SetReal;
