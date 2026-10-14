// MemeCapes launchpad: the small part of @solana/spl-token that the Meteora bonding-curve SDK uses.
// Classic SPL tokens and wrapped SOL only. Token-2022 extension helpers report "no extensions",
// so a Token-2022 mint with transfer fees or hooks is refused by the page before it gets here.
import { PublicKey, TransactionInstruction, SystemProgram } from '@solana/web3.js';
import { Buffer } from 'buffer';

export const TOKEN_PROGRAM_ID = new PublicKey('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');
export const TOKEN_2022_PROGRAM_ID = new PublicKey('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb');
export const ASSOCIATED_TOKEN_PROGRAM_ID = new PublicKey('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL');
export const NATIVE_MINT = new PublicKey('So11111111111111111111111111111111111111112');
export const NATIVE_MINT_2022 = new PublicKey('9pan9bMn5HatX4EJdBwg9VgCa7Uz5HL8N1m5D3NdXejP');
export const MAX_FEE_BASIS_POINTS = 10000;
export const ACCOUNT_SIZE = 165, MINT_SIZE = 82;

export class TokenError extends Error { constructor(m) { super(m); this.name = this.constructor.name; } }
export class TokenAccountNotFoundError extends TokenError {}
export class TokenInvalidAccountOwnerError extends TokenError {}
export class TokenInvalidAccountSizeError extends TokenError {}
export class TokenOwnerOffCurveError extends TokenError {}
export class TokenUnsupportedError extends TokenError {}

export const ExtensionType = { Uninitialized: 0, TransferFeeConfig: 1, TransferFeeAmount: 2, MintCloseAuthority: 3, ConfidentialTransferMint: 4,
  ConfidentialTransferAccount: 5, DefaultAccountState: 6, ImmutableOwner: 7, MemoTransfer: 8, NonTransferable: 9, InterestBearingConfig: 10,
  CpiGuard: 11, PermanentDelegate: 12, NonTransferableAccount: 13, TransferHook: 14, TransferHookAccount: 15, MetadataPointer: 18, TokenMetadata: 19,
  GroupPointer: 20, TokenGroup: 21, GroupMemberPointer: 22, TokenGroupMember: 23 };

export function getAssociatedTokenAddressSync(mint, owner, allowOwnerOffCurve = false, programId = TOKEN_PROGRAM_ID, associatedTokenProgramId = ASSOCIATED_TOKEN_PROGRAM_ID) {
  if (!allowOwnerOffCurve && !PublicKey.isOnCurve(owner.toBuffer())) throw new TokenOwnerOffCurveError();
  return PublicKey.findProgramAddressSync([owner.toBuffer(), programId.toBuffer(), mint.toBuffer()], associatedTokenProgramId)[0];
}

export function createAssociatedTokenAccountIdempotentInstruction(payer, associatedToken, owner, mint, programId = TOKEN_PROGRAM_ID, associatedTokenProgramId = ASSOCIATED_TOKEN_PROGRAM_ID) {
  return new TransactionInstruction({
    keys: [
      { pubkey: payer, isSigner: true, isWritable: true },
      { pubkey: associatedToken, isSigner: false, isWritable: true },
      { pubkey: owner, isSigner: false, isWritable: false },
      { pubkey: mint, isSigner: false, isWritable: false },
      { pubkey: SystemProgram.programId, isSigner: false, isWritable: false },
      { pubkey: programId, isSigner: false, isWritable: false },
    ],
    programId: associatedTokenProgramId,
    data: Buffer.from([1]),
  });
}
export function createAssociatedTokenAccountInstruction(payer, associatedToken, owner, mint, programId = TOKEN_PROGRAM_ID, associatedTokenProgramId = ASSOCIATED_TOKEN_PROGRAM_ID) {
  const ix = createAssociatedTokenAccountIdempotentInstruction(payer, associatedToken, owner, mint, programId, associatedTokenProgramId);
  ix.data = Buffer.alloc(0); return ix;
}

function signerKeys(authority, multiSigners) {
  if (multiSigners && multiSigners.length) throw new TokenUnsupportedError('multisig authorities are not supported here');
  return [{ pubkey: authority, isSigner: true, isWritable: false }];
}
export function createCloseAccountInstruction(account, destination, authority, multiSigners = [], programId = TOKEN_PROGRAM_ID) {
  return new TransactionInstruction({ keys: [{ pubkey: account, isSigner: false, isWritable: true }, { pubkey: destination, isSigner: false, isWritable: true }, ...signerKeys(authority, multiSigners)], programId, data: Buffer.from([9]) });
}
export function createSyncNativeInstruction(account, programId = TOKEN_PROGRAM_ID) {
  return new TransactionInstruction({ keys: [{ pubkey: account, isSigner: false, isWritable: true }], programId, data: Buffer.from([17]) });
}
function u64le(n) { const b = Buffer.alloc(8); b.writeBigUInt64LE(BigInt(n)); return b; }
export function createTransferCheckedInstruction(source, mint, destination, owner, amount, decimals, multiSigners = [], programId = TOKEN_PROGRAM_ID) {
  return new TransactionInstruction({ keys: [{ pubkey: source, isSigner: false, isWritable: true }, { pubkey: mint, isSigner: false, isWritable: false }, { pubkey: destination, isSigner: false, isWritable: true }, ...signerKeys(owner, multiSigners)],
    programId, data: Buffer.concat([Buffer.from([12]), u64le(amount), Buffer.from([decimals])]) });
}
export function createBurnCheckedInstruction(account, mint, owner, amount, decimals, multiSigners = [], programId = TOKEN_PROGRAM_ID) {
  return new TransactionInstruction({ keys: [{ pubkey: account, isSigner: false, isWritable: true }, { pubkey: mint, isSigner: false, isWritable: true }, ...signerKeys(owner, multiSigners)],
    programId, data: Buffer.concat([Buffer.from([15]), u64le(amount), Buffer.from([decimals])]) });
}
export async function createTransferCheckedWithTransferHookInstruction() { throw new TokenUnsupportedError('transfer-hook tokens are not supported on the MemeCapes launchpad'); }

const pk = (d, o) => new PublicKey(d.subarray(o, o + 32));
export function unpackAccount(address, info, programId = TOKEN_PROGRAM_ID) {
  if (!info) throw new TokenAccountNotFoundError();
  if (!info.owner.equals(programId)) throw new TokenInvalidAccountOwnerError();
  const d = Buffer.from(info.data);
  if (d.length < ACCOUNT_SIZE) throw new TokenInvalidAccountSizeError();
  const state = d[108], hasDel = d.readUInt32LE(72), hasNative = d.readUInt32LE(109), hasClose = d.readUInt32LE(129);
  return { address, mint: pk(d, 0), owner: pk(d, 32), amount: d.readBigUInt64LE(64), delegate: hasDel ? pk(d, 76) : null, delegatedAmount: d.readBigUInt64LE(121),
    isInitialized: state !== 0, isFrozen: state === 2, isNative: !!hasNative, rentExemptReserve: hasNative ? d.readBigUInt64LE(113) : null,
    closeAuthority: hasClose ? pk(d, 133) : null, tlvData: d.subarray(ACCOUNT_SIZE + 1) };
}
export async function getAccount(connection, address, commitment, programId = TOKEN_PROGRAM_ID) {
  return unpackAccount(address, await connection.getAccountInfo(address, commitment), programId);
}
export function unpackMint(address, info, programId = TOKEN_PROGRAM_ID) {
  if (!info) throw new TokenAccountNotFoundError();
  if (!info.owner.equals(programId)) throw new TokenInvalidAccountOwnerError();
  const d = Buffer.from(info.data);
  if (d.length < MINT_SIZE) throw new TokenInvalidAccountSizeError();
  return { address, mintAuthority: d.readUInt32LE(0) ? pk(d, 4) : null, supply: d.readBigUInt64LE(36), decimals: d[44], isInitialized: d[45] !== 0,
    freezeAuthority: d.readUInt32LE(46) ? pk(d, 50) : null, tlvData: d.length > ACCOUNT_SIZE ? d.subarray(ACCOUNT_SIZE + 1) : Buffer.alloc(0) };
}
export async function getMint(connection, address, commitment, programId = TOKEN_PROGRAM_ID) {
  return unpackMint(address, await connection.getAccountInfo(address, commitment), programId);
}

// Token-2022 extensions: read the TLV list so the page can refuse mints it does not support.
export function getExtensionTypes(tlvData) {
  const out = []; let i = 0; const d = Buffer.from(tlvData || []);
  while (i + 4 <= d.length) { const t = d.readUInt16LE(i), l = d.readUInt16LE(i + 2); if (t === 0) break; out.push(t); i += 4 + l; }
  return out;
}
export function getTransferFeeConfig(mint) { return getExtensionTypes(mint && mint.tlvData).includes(ExtensionType.TransferFeeConfig) ? (() => { throw new TokenUnsupportedError('transfer-fee tokens are not supported'); })() : null; }
export function getTransferHook(mint) { return getExtensionTypes(mint && mint.tlvData).includes(ExtensionType.TransferHook) ? (() => { throw new TokenUnsupportedError('transfer-hook tokens are not supported'); })() : null; }
export function getEpochFee() { return { epoch: 0n, maximumFee: 0n, transferFeeBasisPoints: 0 }; }
export function calculateFee() { return 0n; }
