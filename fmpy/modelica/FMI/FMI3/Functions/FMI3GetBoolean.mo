within FMI.FMI3.Functions;
impure function FMI3GetBoolean
  input Internal.ExternalFMU externalFMU;
    input Integer valueReferences[nValueReferences];
    input Integer nValueReferences;
    output Boolean values[nValueReferences];
    external"C" FMU_FMI3GetBoolean(externalFMU, valueReferences, nValueReferences, values) annotation (Library="ModelicaFMI");
end FMI3GetBoolean;
