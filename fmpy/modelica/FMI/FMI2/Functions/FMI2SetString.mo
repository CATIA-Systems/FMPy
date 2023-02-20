within FMI.FMI2.Functions;
impure function FMI2SetString
  input Internal.ExternalFMU externalFMU;
    input Integer vr[nvr];
    input Integer nvr;
    input String value[nvr];
    external"C" FMU_FMI2SetString(externalFMU, vr, nvr, value) annotation (Library="ModelicaFMI");
end FMI2SetString;
