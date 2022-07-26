within FMI.FMI3.Functions;
impure function FMI3GetInt32
  input Internal.ExternalFMU externalFMU;
    input Integer valueReferences[nValueReferences];
    input Integer nValueReferences;
    output Integer values[nValueReferences];
    external"C" FMU_FMI3GetInt32(externalFMU, valueReferences, nValueReferences, values) annotation (Library="ModelicaFMI");
end FMI3GetInt32;
