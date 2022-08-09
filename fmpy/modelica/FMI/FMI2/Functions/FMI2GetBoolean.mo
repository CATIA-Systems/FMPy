within FMI.FMI2.Functions;
impure function FMI2GetBoolean
  input Internal.ExternalFMU externalFMU;
    input Integer vr[nvr];
    input Integer nvr;
    output Boolean value[nvr];
    external"C" FMU_FMI2GetBoolean(externalFMU, vr, nvr, value) annotation (Library="ModelicaFMI");
end FMI2GetBoolean;
