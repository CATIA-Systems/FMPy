within FMI.FMI3;
impure function FMI3SetFloat64
  input Internal.ExternalFMU externalFMU;
    input Integer valueReferences[nValueReferences];
    input Integer nValueReferences;
    input Real values[nValueReferences];
    external"C" FMU_FMI3SetFloat64(externalFMU, valueReferences, nValueReferences, values) annotation (Library="ModelicaFMI");
end FMI3SetFloat64;
