within FMI.FMI2;
impure function FMI2SetBoolean
  input Internal.ExternalFMU externalFMU;
    input Integer vr[nvr];
    input Integer nvr;
    input Boolean value[nvr];
    external"C" FMU_FMI2SetBoolean(externalFMU, vr, nvr, value) annotation (Library="ModelicaFMI");
end FMI2SetBoolean;
