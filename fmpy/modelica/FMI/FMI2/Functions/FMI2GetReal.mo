within FMI.FMI2.Functions;
impure function FMI2GetReal
  input Internal.ExternalFMU externalFMU;
    input Integer vr[nvr];
    input Integer nvr;
    output Real value[nvr];
    external"C" FMU_FMI2GetReal(externalFMU, vr, nvr, value) annotation (Library="ModelicaFMI");
end FMI2GetReal;
