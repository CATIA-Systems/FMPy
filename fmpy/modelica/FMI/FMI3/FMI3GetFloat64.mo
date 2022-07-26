within FMI.FMI3;
impure function FMI3GetFloat64
  input Internal.ExternalFMU externalFMU;
    input Integer valueReferences[nValueReferences];
    input Integer nValueReferences;
    output Real values[nValueReferences];
    external"C" FMU_FMI3GetFloat64(externalFMU, valueReferences, nValueReferences, values) annotation (Library="ModelicaFMI");
end FMI3GetFloat64;
